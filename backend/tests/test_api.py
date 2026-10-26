import pytest
from fastapi.testclient import TestClient

from app import elexon
from app.main import app

from .synthetic import actual_records, forecast_records

client = TestClient(app, raise_server_exceptions=False)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(
    "origin",
    [
        "https://windpulse-o2cpcudit-tejasshinde7276-8524s-projects.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000",
    ],
)
def test_cors_allows_production_and_local_origins(origin):
    response = client.options(
        "/api/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


def test_cors_rejects_unknown_origin():
    response = client.options(
        "/api/health",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize("value", ["10-01-2026", "2026-13-01", "not-a-date", ""])
def test_malformed_date_is_rejected(value):
    assert client.get("/api/wind/day", params={"date": value}).status_code == 422


def test_missing_date_is_rejected():
    assert client.get("/api/wind/day").status_code == 422


@pytest.mark.parametrize("value", ["2025-12-31", "2026-02-01"])
def test_date_outside_january_2026_is_rejected(value):
    response = client.get("/api/wind/day", params={"date": value})
    assert response.status_code == 422
    assert "between 2026-01-01 and 2026-01-31" in response.json()["detail"]


def test_upstream_failure_becomes_502_without_internals(monkeypatch):
    def broken(day):
        raise elexon.ElexonError("Elexon API timed out")

    monkeypatch.setattr(elexon, "fetch_actual_wind", broken)
    response = client.get("/api/wind/day", params={"date": "2026-01-10"})
    assert response.status_code == 502
    assert "Traceback" not in response.text


def test_successful_response_shape(monkeypatch):
    monkeypatch.setattr(elexon, "fetch_actual_wind", lambda day: actual_records([100] * 48))
    monkeypatch.setattr(
        elexon, "fetch_wind_forecasts",
        lambda start, end: forecast_records([90] * 48, "2026-01-09T08:00:00Z"),
    )
    response = client.get("/api/wind/day", params={"date": "2026-01-10"})
    body = response.json()
    assert response.status_code == 200
    assert body["unit"] == "MW"
    assert len(body["points"]) == 48
    assert body["metrics"]["mae_mw"] == 10


def test_unexpected_error_is_hidden(monkeypatch):
    def boom(day):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(elexon, "fetch_actual_wind", boom)
    response = client.get("/api/wind/day", params={"date": "2026-01-10"})
    assert response.status_code == 500
    assert "secret" not in response.text
