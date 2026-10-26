from datetime import date

import pytest

from app import elexon, service

from .synthetic import actual_records, forecast_records

DAY = date(2026, 1, 10)  # cutoff is 2026-01-09 09:20 UTC with the default setting
BEFORE_CUTOFF = "2026-01-09T08:00:00Z"
AFTER_CUTOFF = "2026-01-09T10:00:00Z"


@pytest.fixture
def fake_elexon(monkeypatch):
    def install(actuals, forecasts):
        monkeypatch.setattr(elexon, "fetch_actual_wind", lambda day: actuals)
        monkeypatch.setattr(elexon, "fetch_wind_forecasts", lambda start, end: forecasts)

    return install


def test_full_day_matches_periods_and_ignores_late_forecast(fake_elexon):
    actuals = actual_records([100] * 48)
    forecasts = forecast_records([110] * 48, BEFORE_CUTOFF) + forecast_records([999] * 48, AFTER_CUTOFF)
    fake_elexon(actuals, forecasts)

    result = service.analyse_day(DAY)

    assert result["coverage"]["expected_periods"] == 48
    assert result["coverage"]["matched_periods"] == 48
    assert {p["forecast_mw"] for p in result["points"]} == {110}
    assert result["forecast_published_at"]["latest"] == BEFORE_CUTOFF
    assert result["metrics"]["mae_mw"] == pytest.approx(10)
    assert result["metrics"]["overforecast_periods"] == 48


def test_unmatched_periods_are_counted(fake_elexon):
    # Forecasts exist for the first 24 half-hours only.
    fake_elexon(actual_records([100] * 48), forecast_records([90] * 24, BEFORE_CUTOFF))

    result = service.analyse_day(DAY)

    assert result["coverage"]["forecast_periods"] == 24
    assert result["coverage"]["matched_periods"] == 24
    assert result["coverage"]["unmatched_periods"] == 24
    assert result["metrics"]["mae_mw"] == pytest.approx(10)
    assert result["shortfall"]["periods"] == 24
    assert result["shortfall"]["energy_mwh"] == pytest.approx(10 * 24 * 0.5)


def test_metrics_withheld_when_too_few_matches(fake_elexon):
    fake_elexon(actual_records([100] * 48), forecast_records([90] * 5, BEFORE_CUTOFF))

    result = service.analyse_day(DAY)

    assert result["metrics"] is None
    assert "accuracy metrics are not shown" in result["metrics_note"]
    assert result["coverage"]["matched_periods"] == 5


def test_only_late_forecasts_means_no_forecast(fake_elexon):
    fake_elexon(actual_records([100] * 48), forecast_records([999] * 48, AFTER_CUTOFF))

    result = service.analyse_day(DAY)

    assert result["coverage"]["forecast_periods"] == 0
    assert result["forecast_published_at"]["latest"] is None
    assert result["summary"]["actual_mean_mw"] == 100


def test_no_data_at_all(fake_elexon):
    fake_elexon([], [])

    result = service.analyse_day(DAY)

    assert result["coverage"]["matched_periods"] == 0
    assert result["metrics"] is None
    assert len(result["points"]) == 48


def test_large_errors_are_flagged(fake_elexon):
    forecast = [100] * 47 + [400]  # one big miss, rest exact
    fake_elexon(actual_records([100] * 48), forecast_records(forecast, BEFORE_CUTOFF))

    result = service.analyse_day(DAY)

    flagged = [p for p in result["points"] if p["large_error"]]
    assert len(flagged) == 1
    assert flagged[0]["error_mw"] == 300


@pytest.mark.parametrize("day", [date(2025, 12, 31), date(2026, 2, 1)])
def test_dates_outside_january_2026_are_rejected(day):
    with pytest.raises(service.DateOutOfRange):
        service.validate_delivery_date(day)


def test_boundary_dates_are_accepted():
    service.validate_delivery_date(date(2026, 1, 1))
    service.validate_delivery_date(date(2026, 1, 31))
