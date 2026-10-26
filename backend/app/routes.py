"""HTTP routes."""
import logging
from datetime import date

from fastapi import APIRouter, HTTPException, Query

from .elexon import ElexonError
from .service import DateOutOfRange, analyse_day

logger = logging.getLogger("windpulse")
router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/wind/day")
def wind_day(date_: str = Query(alias="date", description="Delivery date, YYYY-MM-DD (January 2026)")):
    try:
        day = date.fromisoformat(date_)
    except ValueError:
        raise HTTPException(status_code=422, detail="date must be in YYYY-MM-DD format")

    try:
        return analyse_day(day)
    except DateOutOfRange as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ElexonError as exc:
        logger.warning("Elexon request failed for %s: %s", day, exc)
        raise HTTPException(status_code=502, detail=f"Could not get data from Elexon: {exc}")
