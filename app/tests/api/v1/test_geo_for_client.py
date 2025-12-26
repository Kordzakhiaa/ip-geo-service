import pytest
from fastapi import HTTPException, status
from httpx import RequestError, TimeoutException

from app.api.v1.endpoints import geo_for_client

PATCH_TARGET = "app.api.v1.endpoints.get_geo_for_ip"


async def _return(resp):
    return resp


async def _raise_404(ip):
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="private range")


async def _raise_request_error(ip):
    raise RequestError("Connection failed")


async def _raise_timeout(ip):
    raise TimeoutException("Request timed out")


@pytest.mark.asyncio
async def test_geo_for_client_success(monkeypatch, make_request, fake_geo_response):
    ip = "8.8.8.8"
    monkeypatch.setattr(PATCH_TARGET, lambda *a, **k: _return(fake_geo_response(ip)))
    request = make_request(ip)

    response = await geo_for_client(request)
    assert response.country == "United States"
    assert response.region == "California"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "client_ip, expected_status, expected_detail, fake_get",
    [
        (
            "999.999.999.999",
            status.HTTP_400_BAD_REQUEST,
            "Invalid client IP address",
            None,
        ),
        ("172.18.0.11", status.HTTP_404_NOT_FOUND, "private range", _raise_404),
        (
            "8.8.8.8",
            status.HTTP_502_BAD_GATEWAY,
            "Failed to fetch data from geolocation service",
            _raise_request_error,
        ),
        (
            "8.8.8.8",
            status.HTTP_502_BAD_GATEWAY,
            "Failed to fetch data from geolocation service",
            _raise_timeout,
        ),
    ],
    ids=["invalid-ip", "private-ip-404", "request-error-502", "timeout-502"],
)
async def test_geo_for_client_errors(
    monkeypatch, make_request, client_ip, expected_status, expected_detail, fake_get
):
    if fake_get:
        monkeypatch.setattr(PATCH_TARGET, fake_get)

    request = make_request(client_ip)
    with pytest.raises(HTTPException) as exc:
        await geo_for_client(request)

    assert exc.value.status_code == expected_status
    assert expected_detail in exc.value.detail


@pytest.mark.asyncio
async def test_geo_for_client_malformed_response(
    monkeypatch, make_request, fake_geo_response
):
    ip = "8.8.8.8"
    resp = fake_geo_response(
        ip,
        country="Neverland",
        region="",
        city="",
        latitude=0.0,
        longitude=0.0,
        timezone="",
        isp="",
    )
    monkeypatch.setattr(PATCH_TARGET, lambda *a, **k: _return(resp))

    request = make_request(ip)
    response = await geo_for_client(request)

    assert response.country == "Neverland"
    assert response.latitude == 0.0
    assert response.longitude == 0.0
