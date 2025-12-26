from types import SimpleNamespace

import pytest
from fastapi import HTTPException, status

from app.api.v1.endpoints import geo_by_ip


def make_fake_get(response_data=None, raise_exc=None):
    """
    Returns an async function to patch httpx.AsyncClient.get.

    :param response_data: dict, returned from .json() if no exception
    :param raise_exc: Exception class instance to raise instead of returning
    """

    async def _fake_get(*args, **kwargs):
        if raise_exc:
            raise raise_exc
        return SimpleNamespace(json=lambda: response_data)

    return _fake_get


@pytest.mark.asyncio
async def test_geo_by_ip_success(monkeypatch):
    sample_ip = "8.8.8.8"
    payload = {
        "status": "success",
        "country": "United States",
        "regionName": "California",
        "city": "Mountain View",
        "lat": 37.386,
        "lon": -122.0838,
        "timezone": "America/Los_Angeles",
        "isp": "Google LLC",
    }

    monkeypatch.setattr(
        "app.services.ip_geolocation.httpx.AsyncClient.get",
        make_fake_get(payload),
    )

    resp = await geo_by_ip(sample_ip)
    assert resp.ip == sample_ip
    assert resp.country == "United States"
    assert resp.region == "California"
    assert resp.city == "Mountain View"
    assert resp.latitude == 37.386
    assert resp.longitude == -122.0838
    assert resp.timezone == "America/Los_Angeles"
    assert resp.isp == "Google LLC"


@pytest.mark.asyncio
async def test_geo_by_ip_invalid_ip():
    from app.api.v1.endpoints import geo_by_ip as endpoint

    invalid_ip = "999.999.999.999"

    with pytest.raises(HTTPException) as exc:
        await endpoint(invalid_ip)
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid IP address" in exc.value.detail


@pytest.mark.asyncio
async def test_geo_by_ip_not_found(monkeypatch):
    monkeypatch.setattr(
        "app.services.ip_geolocation.httpx.AsyncClient.get",
        make_fake_get({"status": "fail"}),
    )

    from app.api.v1.endpoints import geo_by_ip as endpoint

    sample_ip = "8.8.8.8"

    with pytest.raises(HTTPException) as exc:
        await endpoint(sample_ip)
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert "IP information not found" in exc.value.detail


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exc_class",
    [("RequestError", "Connection failed"), ("TimeoutException", "Request timed out")],
)
async def test_geo_by_ip_network_errors(monkeypatch, exc_class):
    from httpx import RequestError, TimeoutException

    exc_map = {
        "RequestError": RequestError("Connection failed"),
        "TimeoutException": TimeoutException("Request timed out"),
    }
    monkeypatch.setattr(
        "app.services.ip_geolocation.httpx.AsyncClient.get",
        make_fake_get(raise_exc=exc_map[exc_class[0]]),
    )

    from app.api.v1.endpoints import geo_by_ip as endpoint

    sample_ip = "8.8.8.8"

    with pytest.raises(HTTPException) as exc:
        await endpoint(sample_ip)
    assert exc.value.status_code == status.HTTP_502_BAD_GATEWAY
    assert "Failed to fetch data from geolocation service" in exc.value.detail


@pytest.mark.asyncio
async def test_geo_by_ip_malformed_response(monkeypatch):
    malformed_payload = {
        "status": "success",
        "country": "Neverland",
        "regionName": "",
        "city": "",
        # lat, lon, timezone, isp missing
    }

    monkeypatch.setattr(
        "app.services.ip_geolocation.httpx.AsyncClient.get",
        make_fake_get(malformed_payload),
    )

    resp = await geo_by_ip("8.8.8.8")
    assert resp.ip == "8.8.8.8"
    assert resp.country == "Neverland"
    assert resp.latitude == 0.0
    assert resp.longitude == 0.0
    assert resp.timezone == ""
    assert resp.isp == ""
