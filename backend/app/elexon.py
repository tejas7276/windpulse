"""Thin client for the two Elexon BMRS dataset streams used by WindPulse."""
import threading
import time
from datetime import date, datetime, timezone

import requests

from . import config


class ElexonError(Exception):
    """The Elexon API could not be reached or returned something unusable."""


_cache = {}  # (path, sorted params) -> (stored_at, records)
_cache_lock = threading.Lock()
_MAX_CACHE_ENTRIES = 64


def _cached(key):
    with _cache_lock:
        hit = _cache.get(key)
    if hit and time.monotonic() - hit[0] < config.CACHE_TTL_SECONDS:
        return hit[1]
    return None


def _store(key, records):
    with _cache_lock:
        if len(_cache) >= _MAX_CACHE_ENTRIES:
            _cache.pop(next(iter(_cache)))
        _cache[key] = (time.monotonic(), records)


def _get_records(path, params):
    key = (path, tuple(sorted(params.items())))
    cached = _cached(key)
    if cached is not None:
        return cached

    try:
        response = requests.get(
            f"{config.ELEXON_BASE_URL}{path}",
            params={**params, "format": "json"},
            timeout=config.ELEXON_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        body = response.json()
    except requests.Timeout as exc:
        raise ElexonError("Elexon API timed out") from exc
    except requests.RequestException as exc:
        raise ElexonError(f"Elexon API request failed ({exc.__class__.__name__})") from exc
    except ValueError as exc:
        raise ElexonError("Elexon API returned invalid JSON") from exc

    # The stream endpoints return a bare JSON array; tolerate a {"data": [...]} wrapper.
    records = body.get("data") if isinstance(body, dict) else body
    if not isinstance(records, list):
        raise ElexonError("Unexpected Elexon response shape")

    # Don't cache empty results: an empty answer may just be a temporary gap upstream.
    if records:
        _store(key, records)
    return records


def _iso_utc(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_actual_wind(settlement_date: date):
    """FUELHH half-hourly outturn for one settlement date, WIND only."""
    return _get_records(
        "/datasets/FUELHH/stream",
        {
            "settlementDateFrom": settlement_date.isoformat(),
            "settlementDateTo": settlement_date.isoformat(),
            "fuelType": "WIND",
        },
    )


def fetch_wind_forecasts(published_from: datetime, published_to: datetime):
    """WINDFOR publications made in the given window (every publication, not just the latest)."""
    return _get_records(
        "/datasets/WINDFOR/stream",
        {
            "publishDateTimeFrom": _iso_utc(published_from),
            "publishDateTimeTo": _iso_utc(published_to),
        },
    )
