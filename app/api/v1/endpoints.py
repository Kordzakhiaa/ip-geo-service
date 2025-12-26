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
    return {"status": "ok"}


@router.get(
    "/geo/{ip}",
    response_model=GeoResponse,
    responses={status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse}},
)
async def geo_by_ip(ip: str):
    if not validate_ipv4(ip):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid IP address"
        )

    try:
        return await get_geo_for_ip(ip)
    except (RequestError, TimeoutException) as e:
        logger.exception(f"HTTP request failed for IP {ip}, error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch data from geolocation service",
        )


@router.get("/geo", response_model=GeoResponse)
async def geo_for_client(request: Request):
    client_ip = request.client.host
    return await get_geo_for_ip(client_ip)
