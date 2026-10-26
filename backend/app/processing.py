"""Turn raw Elexon records into clean pandas frames."""
import pandas as pd


def _to_frame(records, columns):
    frame = pd.DataFrame(records)
    for column in columns:
        if column not in frame.columns:
            frame[column] = None
    return frame


def clean_actuals(records):
    """Return (frame, stats). Frame columns: start_time (UTC), actual_mw; one row per start_time."""
    frame = _to_frame(records, ["fuelType", "startTime", "publishTime", "generation"])
    stats = {"raw_records": len(frame), "invalid_records": 0, "duplicate_records": 0}

    frame = frame[frame["fuelType"] == "WIND"].copy()
    frame["start_time"] = pd.to_datetime(frame["startTime"], utc=True, errors="coerce")
    frame["publish_time"] = pd.to_datetime(frame["publishTime"], utc=True, errors="coerce")
    frame["actual_mw"] = pd.to_numeric(frame["generation"], errors="coerce")

    valid = frame.dropna(subset=["start_time", "actual_mw"])
    stats["invalid_records"] = len(frame) - len(valid)

    # If a period was published more than once, the latest publication wins.
    valid = valid.sort_values(["start_time", "publish_time"], na_position="first")
    deduped = valid.drop_duplicates("start_time", keep="last")
    stats["duplicate_records"] = len(valid) - len(deduped)

    return deduped[["start_time", "actual_mw"]].reset_index(drop=True), stats


def clean_forecasts(records):
    """Return (frame, stats). Frame columns: start_time, publish_time (UTC), forecast_mw."""
    frame = _to_frame(records, ["startTime", "publishTime", "generation"])
    stats = {"raw_records": len(frame), "invalid_records": 0, "duplicate_records": 0}

    frame["start_time"] = pd.to_datetime(frame["startTime"], utc=True, errors="coerce")
    frame["publish_time"] = pd.to_datetime(frame["publishTime"], utc=True, errors="coerce")
    frame["forecast_mw"] = pd.to_numeric(frame["generation"], errors="coerce")

    # Without a publish_time we cannot tell whether a row was available at the cutoff.
    valid = frame.dropna(subset=["start_time", "publish_time", "forecast_mw"])
    stats["invalid_records"] = len(frame) - len(valid)

    deduped = valid.drop_duplicates(["start_time", "publish_time"], keep="last")
    stats["duplicate_records"] = len(valid) - len(deduped)

    return deduped[["start_time", "publish_time", "forecast_mw"]].reset_index(drop=True), stats
