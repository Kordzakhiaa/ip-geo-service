import logging

import httpx
from fastapi import HTTPException, status

from app.api.v1.models import GeoResponse
from app.core.settings import IPSettings

logger = logging.getLogger(__name__)

IP_SETTINGS = IPSettings()


async def get_geo_for_ip(ip: str) -> GeoResponse:
    async with httpx.AsyncClient(timeout=IP_SETTINGS.IP_API_TIMEOUT) as client:
        try:
            resp = await client.get(IP_SETTINGS.IP_API_URL.format(ip=ip))
            data = resp.json()
        except httpx.RequestError as e:
            logger.error(f"HTTP request failed for IP {ip}: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to fetch data from geolocation service",
            )

    if data.get("status") != "success":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="IP information not found"
        )

    return GeoResponse(
        ip=ip,
        country=data.get("country", ""),
        region=data.get("regionName", ""),
        city=data.get("city", ""),
        latitude=data.get("lat", 0.0),
        longitude=data.get("lon", 0.0),
        timezone=data.get("timezone", ""),
        isp=data.get("isp", ""),
    )
