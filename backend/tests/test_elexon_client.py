"""Client behaviour with `requests.get` replaced by a fake (no network)."""
from datetime import date

import pytest
import requests

from app import elexon


class FakeResponse:
    def __init__(self, body, status=200):
        self._body = body
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")

    def json(self):
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


@pytest.fixture(autouse=True)
def clear_cache():
    elexon._cache.clear()


def patch_get(monkeypatch, outcome):
    calls = []

    def fake_get(url, params, timeout):
        calls.append((url, params, timeout))
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(elexon.requests, "get", fake_get)
    return calls


def test_sends_expected_parameters(monkeypatch):
    calls = patch_get(monkeypatch, FakeResponse([{"x": 1}]))
    elexon.fetch_actual_wind(date(2026, 1, 10))
    url, params, timeout = calls[0]
    assert url.endswith("/datasets/FUELHH/stream")
    assert params == {
        "settlementDateFrom": "2026-01-10",
        "settlementDateTo": "2026-01-10",
        "fuelType": "WIND",
        "format": "json",
    }
    assert timeout > 0


def test_repeat_calls_use_the_cache(monkeypatch):
    calls = patch_get(monkeypatch, FakeResponse([{"x": 1}]))
    elexon.fetch_actual_wind(date(2026, 1, 10))
    elexon.fetch_actual_wind(date(2026, 1, 10))
    assert len(calls) == 1


def test_empty_results_are_not_cached(monkeypatch):
    calls = patch_get(monkeypatch, FakeResponse([]))
    elexon.fetch_actual_wind(date(2026, 1, 10))
    elexon.fetch_actual_wind(date(2026, 1, 10))
    assert len(calls) == 2


def test_wrapped_data_array_is_accepted(monkeypatch):
    patch_get(monkeypatch, FakeResponse({"data": [{"x": 1}]}))
    assert elexon.fetch_actual_wind(date(2026, 1, 10)) == [{"x": 1}]


@pytest.mark.parametrize(
    "outcome",
    [
        requests.Timeout(),
        requests.ConnectionError(),
        FakeResponse([], status=500),
        FakeResponse(ValueError("bad json")),
        FakeResponse({"unexpected": "shape"}),
    ],
)
def test_failures_become_elexon_error(monkeypatch, outcome):
    patch_get(monkeypatch, outcome)
    with pytest.raises(elexon.ElexonError):
        elexon.fetch_actual_wind(date(2026, 1, 10))
