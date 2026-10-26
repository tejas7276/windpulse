"""Builds the full analysis for one delivery date."""
from datetime import date, timedelta

import pandas as pd

from . import config, elexon
from .metrics import accuracy_metrics, add_errors
from .processing import clean_actuals, clean_forecasts
from .selection import decision_cutoff, delivery_periods, select_latest_forecasts


class DateOutOfRange(ValueError):
    pass


def validate_delivery_date(day: date) -> None:
    if not config.ANALYSIS_START <= day <= config.ANALYSIS_END:
        raise DateOutOfRange(
            f"Date must be between {config.ANALYSIS_START} and {config.ANALYSIS_END}"
        )


def _number(value):
    """NaN -> None so the value serialises as JSON null."""
    return None if pd.isna(value) else round(float(value), 3)


def _iso(timestamp):
    return None if pd.isna(timestamp) else timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_points(errors: pd.DataFrame) -> list:
    """One JSON-ready dict per half-hour, in UTC order, with the label in UK local time."""
    local_times = errors["start_time"].dt.tz_convert(config.UK_TZ).dt.strftime("%H:%M")
    return [
        {
            "start_time": _iso(row.start_time),
            "local_time": local_time,
            "forecast_mw": _number(row.forecast_mw),
            "actual_mw": _number(row.actual_mw),
            "error_mw": _number(row.error_mw),
            "shortfall_mw": _number(row.shortfall_mw),
            "large_error": bool(row.large_error),
            "forecast_published_at": _iso(row.publish_time),
        }
        for row, local_time in zip(errors.itertuples(), local_times)
    ]


def analyse_day(day: date) -> dict:
    validate_delivery_date(day)
    periods = delivery_periods(day)
    cutoff = decision_cutoff(day)

    actual_records = elexon.fetch_actual_wind(day)
    forecast_records = elexon.fetch_wind_forecasts(
        cutoff - timedelta(hours=config.FORECAST_LOOKBACK_HOURS), cutoff
    )

    actuals, actual_stats = clean_actuals(actual_records)
    forecasts, forecast_stats = clean_forecasts(forecast_records)

    # Forecasts are only filtered to this delivery day after the cutoff rule is applied.
    selected = select_latest_forecasts(forecasts, cutoff)
    selected = selected[selected["start_time"].isin(periods)]
    actuals = actuals[actuals["start_time"].isin(periods)]

    table = pd.DataFrame({"start_time": periods})
    table = table.merge(selected, on="start_time", how="left").merge(actuals, on="start_time", how="left")

    matched_mask = table["forecast_mw"].notna() & table["actual_mw"].notna()
    matched = table[matched_mask]
    errors = add_errors(table)

    metrics = None
    metrics_note = None
    if len(matched) >= config.MIN_MATCHED_PERIODS:
        metrics = accuracy_metrics(matched)
        threshold = config.LARGE_ERROR_FACTOR * metrics["mae_mw"]
        errors["large_error"] = matched_mask & (errors["abs_error_mw"] > threshold)
    else:
        errors["large_error"] = False
        metrics_note = (
            f"Only {len(matched)} half-hours have both a forecast and an actual value "
            f"(minimum {config.MIN_MATCHED_PERIODS}), so accuracy metrics are not shown."
        )

    shortfall_mw = errors.loc[matched_mask, "shortfall_mw"]

    publish_times = table["publish_time"].dropna()
    return {
        "date": day.isoformat(),
        "unit": config.GENERATION_UNIT,
        "decision_cutoff": _iso(pd.Timestamp(cutoff)),
        "decision_cutoff_local": cutoff.astimezone(config.UK_TZ).strftime("%Y-%m-%d %H:%M %Z"),
        "forecast_published_at": {
            "earliest": _iso(publish_times.min()) if len(publish_times) else None,
            "latest": _iso(publish_times.max()) if len(publish_times) else None,
        },
        "coverage": {
            "expected_periods": len(periods),
            "forecast_periods": int(table["forecast_mw"].notna().sum()),
            "actual_periods": int(table["actual_mw"].notna().sum()),
            "matched_periods": int(matched_mask.sum()),
            "unmatched_periods": len(periods) - int(matched_mask.sum()),
            "minimum_for_metrics": config.MIN_MATCHED_PERIODS,
            "actual_data_quality": actual_stats,
            "forecast_data_quality": forecast_stats,
        },
        "summary": {
            "forecast_mean_mw": _number(table["forecast_mw"].mean()),
            "forecast_peak_mw": _number(table["forecast_mw"].max()),
            "actual_mean_mw": _number(table["actual_mw"].mean()),
            "actual_peak_mw": _number(table["actual_mw"].max()),
        },
        "metrics": metrics,
        "metrics_note": metrics_note,
        "large_error_threshold_mw": None if metrics is None else _number(config.LARGE_ERROR_FACTOR * metrics["mae_mw"]),
        "shortfall": {
            "periods": int((shortfall_mw > 0).sum()),
            "max_mw": _number(shortfall_mw.max()) if len(shortfall_mw) else None,
            "energy_mwh": _number(shortfall_mw.sum() * config.PERIOD_HOURS) if len(shortfall_mw) else None,
        },
        "points": _build_points(errors),
    }
