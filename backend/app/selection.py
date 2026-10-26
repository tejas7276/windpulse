"""Delivery periods and decision-time forecast selection."""
from datetime import date, datetime, time, timedelta, timezone

import pandas as pd

from . import config


def _local_midnight_utc(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=config.UK_TZ).astimezone(timezone.utc)


def decision_cutoff(delivery_date: date, cutoff_time: time = None) -> datetime:
    """The last moment (UTC) a forecast could inform day-ahead buying for delivery_date.

    That is `cutoff_time` UK local time on the previous calendar day. Building it
    from UK local time keeps it correct across the clock changes in March/October.
    """
    cutoff_time = cutoff_time or config.DECISION_CUTOFF
    local = datetime.combine(delivery_date - timedelta(days=1), cutoff_time, tzinfo=config.UK_TZ)
    return local.astimezone(timezone.utc)


def delivery_periods(delivery_date: date) -> pd.DatetimeIndex:
    """Every half-hour start time (UTC) in the UK local day (46, 48 or 50 on clock-change days)."""
    return pd.date_range(
        _local_midnight_utc(delivery_date),
        _local_midnight_utc(delivery_date + timedelta(days=1)),
        freq="30min",
        inclusive="left",
    )


def select_latest_forecasts(forecasts: pd.DataFrame, cutoff: datetime) -> pd.DataFrame:
    """For each start_time keep the newest forecast published at or before the cutoff.

    Forecasts published after the cutoff are discarded, even if they are the only
    ones for a period; that period then simply has no forecast.
    """
    eligible = forecasts[forecasts["publish_time"] <= pd.Timestamp(cutoff)]
    eligible = eligible.sort_values(["start_time", "publish_time"])
    return eligible.drop_duplicates("start_time", keep="last").reset_index(drop=True)
