"""SYNTHETIC TEST DATA.

Everything here is made up for unit tests. It is never imported by the application
and must never be mixed with real Elexon responses.
"""
import pandas as pd


def half_hours(day="2026-01-10", count=48):
    return list(pd.date_range(f"{day}T00:00:00Z", periods=count, freq="30min"))


def _z(timestamp):
    return timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")


def actual_records(values, day="2026-01-10", fuel="WIND", published="2026-01-10T12:00:00Z"):
    return [
        {"fuelType": fuel, "startTime": _z(start), "publishTime": published, "generation": value}
        for start, value in zip(half_hours(day, len(values)), values)
    ]


def forecast_records(values, published, day="2026-01-10"):
    return [
        {"startTime": _z(start), "publishTime": published, "generation": value}
        for start, value in zip(half_hours(day, len(values)), values)
    ]
