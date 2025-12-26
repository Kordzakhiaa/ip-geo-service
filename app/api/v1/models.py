from pydantic import BaseModel


class GeoResponse(BaseModel):
    ip: str
    country: str
    region: str
    city: str
    latitude: float
    longitude: float
    timezone: str
    isp: str


class ErrorResponse(BaseModel):
    error: str
