from fastapi import APIRouter, Request, status

from app.api.v1.models import GeoResponse, ErrorResponse
from app.services.ip_geolocation import get_geo_for_ip
from app.utils.validators import validate_ipv4

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
def health():
    return {"status": "ok"}


@router.get(
    "/geo/{ip}",
    response_model=GeoResponse,
    responses={status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse}},
)
def geo_by_ip(ip: str):
    if not validate_ipv4(ip):
        return ErrorResponse(error="Invalid IP address")
    return get_geo_for_ip(ip)


@router.get("/geo", response_model=GeoResponse)
def geo_for_client(request: Request):
    client_ip = request.client.host
    return get_geo_for_ip(client_ip)
