"""Settings, read once from environment variables at import time."""
import os
from datetime import date, time
from zoneinfo import ZoneInfo

UK_TZ = ZoneInfo("Europe/London")

# The assignment covers January 2026 only.
ANALYSIS_START = date(2026, 1, 1)
ANALYSIS_END = date(2026, 1, 31)

ELEXON_BASE_URL = os.getenv("ELEXON_BASE_URL", "https://data.elexon.co.uk/bmrs/api/v1")
ELEXON_TIMEOUT_SECONDS = float(os.getenv("ELEXON_TIMEOUT_SECONDS", "30"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

# UK local time on the day before delivery after which a forecast is treated as
# too late to use for day-ahead purchasing. See "Decision cutoff" in the README:
# this value is a configurable assumption, not a verified market rule.
DECISION_CUTOFF = time.fromisoformat(os.getenv("DAY_AHEAD_CUTOFF", "09:20"))

# How far back from the cutoff to ask WINDFOR for publications.
FORECAST_LOOKBACK_HOURS = int(os.getenv("FORECAST_LOOKBACK_HOURS", "72"))

# Below this many matched half-hours the accuracy metrics are withheld.
MIN_MATCHED_PERIODS = int(os.getenv("MIN_MATCHED_PERIODS", "12"))

# A period counts as a "large error" when |error| exceeds this multiple of the day's MAE.
LARGE_ERROR_FACTOR = 1.5

PERIOD_HOURS = 0.5  # one settlement period
GENERATION_UNIT = "MW"

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    if origin.strip()
]
