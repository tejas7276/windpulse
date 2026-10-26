"""Forecast accuracy metrics. Error is always forecast - actual."""
import numpy as np
import pandas as pd


def add_errors(matched: pd.DataFrame) -> pd.DataFrame:
    """Add error_mw, abs_error_mw and shortfall_mw columns to a frame of matched rows."""
    out = matched.copy()
    out["error_mw"] = out["forecast_mw"] - out["actual_mw"]
    out["abs_error_mw"] = out["error_mw"].abs()
    out["shortfall_mw"] = (out["actual_mw"] - out["forecast_mw"]).clip(lower=0)
    return out


def accuracy_metrics(matched: pd.DataFrame) -> dict:
    """MAE, RMSE, MAPE and over/under-forecast counts for rows with both values.

    MAPE skips periods where actual generation is zero (the ratio is undefined);
    mape_observations says how many periods it was based on.
    """
    data = add_errors(matched)
    count = len(data)
    if count == 0:
        raise ValueError("accuracy_metrics needs at least one matched row")

    nonzero = data[data["actual_mw"] != 0]
    mape = (nonzero["abs_error_mw"] / nonzero["actual_mw"].abs()).mean() * 100 if len(nonzero) else None

    over = data[data["error_mw"] > 0]
    under = data[data["error_mw"] < 0]
    return {
        "mae_mw": float(data["abs_error_mw"].mean()),
        "rmse_mw": float(np.sqrt((data["error_mw"] ** 2).mean())),
        "mape_percent": None if mape is None else float(mape),
        "mape_observations": int(len(nonzero)),
        "mean_error_mw": float(data["error_mw"].mean()),
        "overforecast_periods": int(len(over)),
        "underforecast_periods": int(len(under)),
        "mean_overforecast_mw": float(over["error_mw"].mean()) if len(over) else None,
        "mean_underforecast_mw": float(under["error_mw"].mean()) if len(under) else None,
    }
