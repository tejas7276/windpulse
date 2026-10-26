from datetime import date, datetime, time, timezone

import pandas as pd

from app.selection import decision_cutoff, delivery_periods, select_latest_forecasts


def forecast_frame(rows):
    """rows: (start_time, publish_time, forecast_mw) strings/numbers (synthetic)."""
    frame = pd.DataFrame(rows, columns=["start_time", "publish_time", "forecast_mw"])
    frame["start_time"] = pd.to_datetime(frame["start_time"], utc=True)
    frame["publish_time"] = pd.to_datetime(frame["publish_time"], utc=True)
    return frame


def test_cutoff_is_previous_day_in_winter():
    cutoff = decision_cutoff(date(2026, 1, 10), time(9, 20))
    assert cutoff == datetime(2026, 1, 9, 9, 20, tzinfo=timezone.utc)


def test_cutoff_follows_uk_clock_change():
    # 9 June is BST, so 09:20 local is 08:20 UTC.
    cutoff = decision_cutoff(date(2026, 6, 10), time(9, 20))
    assert cutoff == datetime(2026, 6, 9, 8, 20, tzinfo=timezone.utc)


def test_delivery_periods_per_day():
    assert len(delivery_periods(date(2026, 1, 10))) == 48
    assert len(delivery_periods(date(2026, 3, 29))) == 46  # clocks go forward
    assert len(delivery_periods(date(2026, 10, 25))) == 50  # clocks go back


def test_latest_eligible_forecast_is_chosen():
    frame = forecast_frame([
        ("2026-01-10T00:00Z", "2026-01-08T06:00Z", 100),
        ("2026-01-10T00:00Z", "2026-01-09T06:00Z", 120),
        ("2026-01-10T00:00Z", "2026-01-09T09:00Z", 130),
    ])
    chosen = select_latest_forecasts(frame, datetime(2026, 1, 9, 9, 20, tzinfo=timezone.utc))
    assert chosen["forecast_mw"].tolist() == [130]


def test_forecast_after_cutoff_is_excluded():
    frame = forecast_frame([
        ("2026-01-10T00:00Z", "2026-01-09T09:00Z", 130),
        ("2026-01-10T00:00Z", "2026-01-09T09:21Z", 999),
        ("2026-01-10T00:00Z", "2026-01-10T00:00Z", 888),
    ])
    chosen = select_latest_forecasts(frame, datetime(2026, 1, 9, 9, 20, tzinfo=timezone.utc))
    assert chosen["forecast_mw"].tolist() == [130]


def test_forecast_published_exactly_at_cutoff_is_allowed():
    frame = forecast_frame([("2026-01-10T00:00Z", "2026-01-09T09:20Z", 77)])
    chosen = select_latest_forecasts(frame, datetime(2026, 1, 9, 9, 20, tzinfo=timezone.utc))
    assert chosen["forecast_mw"].tolist() == [77]


def test_period_with_only_late_forecasts_gets_none():
    frame = forecast_frame([
        ("2026-01-10T00:00Z", "2026-01-09T09:00Z", 10),
        ("2026-01-10T00:30Z", "2026-01-09T12:00Z", 20),
    ])
    chosen = select_latest_forecasts(frame, datetime(2026, 1, 9, 9, 20, tzinfo=timezone.utc))
    assert chosen["start_time"].dt.strftime("%H:%M").tolist() == ["00:00"]


def test_each_period_selected_independently():
    frame = forecast_frame([
        ("2026-01-10T00:00Z", "2026-01-09T06:00Z", 1),
        ("2026-01-10T00:30Z", "2026-01-09T06:00Z", 2),
        ("2026-01-10T00:30Z", "2026-01-09T08:00Z", 3),
    ])
    chosen = select_latest_forecasts(frame, datetime(2026, 1, 9, 9, 20, tzinfo=timezone.utc))
    assert chosen["forecast_mw"].tolist() == [1, 3]
