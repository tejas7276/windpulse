"""Check the real Elexon responses against what WindPulse assumes.

Run from the backend folder on a machine that can reach the Elexon API:

    python -m scripts.check_elexon 2026-01-10

It prints the field names, row counts, publication behaviour and time resolution
of both datasets so the assumptions in the README can be confirmed.
"""
import sys
from datetime import date, timedelta

import pandas as pd

from app import config, elexon
from app.selection import decision_cutoff


def describe_fields(records):
    return sorted({key for record in records for key in record})


def main(day: date):
    cutoff = decision_cutoff(day)

    actual = elexon.fetch_actual_wind(day)
    print(f"FUELHH ({day}): {len(actual)} records, fields: {describe_fields(actual)}")
    if actual:
        print("  fuelTypes returned:", sorted({r.get("fuelType") for r in actual}))
        print("  sample:", actual[0])

    forecasts = elexon.fetch_wind_forecasts(cutoff - timedelta(hours=config.FORECAST_LOOKBACK_HOURS), cutoff)
    print(f"WINDFOR (published up to {cutoff:%Y-%m-%d %H:%M}Z): {len(forecasts)} records, fields: {describe_fields(forecasts)}")
    if not forecasts:
        return

    frame = pd.DataFrame(forecasts)
    start = pd.to_datetime(frame["startTime"], utc=True)
    publish = pd.to_datetime(frame["publishTime"], utc=True)
    steps = start.drop_duplicates().sort_values().diff().dropna().value_counts().head(3)
    lead_hours = (start - publish).dt.total_seconds() / 3600

    print("  sample:", forecasts[0])
    print(f"  distinct publishTime values: {publish.nunique()} ({publish.min()} to {publish.max()})")
    print(f"  startTime spacing (most common): {dict(steps)}")
    print(f"  lead time publish->start: {lead_hours.min():.1f}h to {lead_hours.max():.1f}h")
    print(f"  records covering {day}: {(start.dt.date == day).sum()}")
    print("  generation range:", frame["generation"].min(), "to", frame["generation"].max(), "(check the unit is MW)")


if __name__ == "__main__":
    main(date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date(2026, 1, 10))
