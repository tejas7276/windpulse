from app.processing import clean_actuals, clean_forecasts

from .synthetic import actual_records, forecast_records


def test_actuals_keep_only_wind():
    records = actual_records([100, 200]) + actual_records([5, 5], fuel="NUCLEAR")
    frame, _ = clean_actuals(records)
    assert frame["actual_mw"].tolist() == [100, 200]


def test_duplicate_actuals_keep_latest_publication():
    older = actual_records([100], published="2026-01-10T01:00:00Z")
    newer = actual_records([150], published="2026-01-10T02:00:00Z")
    frame, stats = clean_actuals(newer + older)
    assert frame["actual_mw"].tolist() == [150]
    assert stats["duplicate_records"] == 1


def test_actuals_drop_missing_and_non_numeric_values():
    frame, stats = clean_actuals(actual_records([100, None, "n/a", 300]))
    assert frame["actual_mw"].tolist() == [100, 300]
    assert stats["invalid_records"] == 2


def test_empty_responses_do_not_crash():
    actuals, _ = clean_actuals([])
    forecasts, _ = clean_forecasts([])
    assert actuals.empty and forecasts.empty


def test_duplicate_forecast_rows_are_removed():
    row = forecast_records([50], published="2026-01-09T06:00:00Z")
    frame, stats = clean_forecasts(row + row)
    assert len(frame) == 1
    assert stats["duplicate_records"] == 1


def test_forecast_without_publish_time_is_dropped():
    rows = forecast_records([50, 60], published="2026-01-09T06:00:00Z")
    rows[1]["publishTime"] = None
    frame, stats = clean_forecasts(rows)
    assert frame["forecast_mw"].tolist() == [50]
    assert stats["invalid_records"] == 1
