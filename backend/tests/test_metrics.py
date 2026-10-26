import math

import pandas as pd
import pytest

from app.metrics import accuracy_metrics, add_errors


def matched(forecast, actual):
    return pd.DataFrame({"forecast_mw": forecast, "actual_mw": actual})


def test_mae_and_rmse():
    # errors (forecast - actual): -2, +2, 0
    result = accuracy_metrics(matched([10, 20, 30], [12, 18, 30]))
    assert result["mae_mw"] == pytest.approx(4 / 3)
    assert result["rmse_mw"] == pytest.approx(math.sqrt(8 / 3))


def test_error_sign_convention():
    result = accuracy_metrics(matched([120, 80], [100, 100]))
    assert result["overforecast_periods"] == 1
    assert result["underforecast_periods"] == 1
    assert result["mean_overforecast_mw"] == pytest.approx(20)
    assert result["mean_underforecast_mw"] == pytest.approx(-20)
    assert result["mean_error_mw"] == pytest.approx(0)


def test_mape_skips_zero_actuals():
    # Only the 100 MW period counts: |110 - 100| / 100 = 10%
    result = accuracy_metrics(matched([110, 5], [100, 0]))
    assert result["mape_percent"] == pytest.approx(10)
    assert result["mape_observations"] == 1
    # MAE and RMSE still use both periods.
    assert result["mae_mw"] == pytest.approx(7.5)


def test_mape_is_none_when_every_actual_is_zero():
    result = accuracy_metrics(matched([5, 6], [0, 0]))
    assert result["mape_percent"] is None
    assert result["mape_observations"] == 0


def test_shortfall_is_never_negative():
    out = add_errors(matched([100, 50], [80, 70]))
    assert out["shortfall_mw"].tolist() == [0, 20]


def test_no_matched_rows_is_an_error():
    with pytest.raises(ValueError):
        accuracy_metrics(matched([], []))
