from app.api.v1.models import GeoResponse


def get_geo_for_ip(ip: str) -> GeoResponse:
    # TODO: integrate with 3rd-party IP geolocation API or local DB

    # Example placeholder response
    return GeoResponse(
        ip=ip,
        country="Unknown",
        region="Unknown",
        city="Unknown",
        latitude=0.0,
        longitude=0.0,
        timezone="UTC",
        isp="Unknown",
    )
