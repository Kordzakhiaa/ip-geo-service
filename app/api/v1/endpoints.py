import logging

from fastapi import APIRouter, Request, status, HTTPException
from httpx import RequestError, TimeoutException

from app.api.v1.models import GeoResponse, ErrorResponse
from app.services.ip_geolocation import get_geo_for_ip
from app.utils.validators import validate_ipv4

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health", status_code=status.HTTP_200_OK)
def health():
    """Simple liveness endpoint to check service health."""
    return {"status": "ok"}


@router.get(
    "/geo/{ip}",
    response_model=GeoResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_502_BAD_GATEWAY: {"model": ErrorResponse},
    },
)
async def geo_by_ip(ip: str) -> GeoResponse:
    """
    Look up geolocation for a specific IP address.

    - Validates IPv4 format.
    - Returns GeoResponse on success.
    - Raises HTTP 400 for invalid IP, 502 for external service failures.
    """
    if not validate_ipv4(ip):
        logger.debug(f"Invalid IP received in geo_by_ip: {ip}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid IP address"
        )

    try:
        return await get_geo_for_ip(ip)
    except (RequestError, TimeoutException) as e:
        logger.exception(f"HTTP request failed for IP {ip}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch data from geolocation service",
        )


@router.get(
    "/geo",
    response_model=GeoResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_502_BAD_GATEWAY: {"model": ErrorResponse},
    },
)
async def geo_for_client(request: Request) -> GeoResponse:
    """
    Look up geolocation for the requesting client's IP address.

    - Automatically detects the client's IP from request.
    - Validates IPv4 format.
    - Returns GeoResponse on success.
    - Handles private IPs and external API failures gracefully.
    """
    client_ip = request.client.host

    if not validate_ipv4(client_ip):
        # Invalid or private IP from request
        logger.debug(
            f"Invalid client IP detected: {client_ip} (headers={dict(request.headers)})"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid client IP address: {client_ip}",
        )

    try:
        return await get_geo_for_ip(client_ip)
    except (RequestError, TimeoutException) as e:
        logger.exception(f"HTTP request failed for client IP {client_ip}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch data from geolocation service",
        )
