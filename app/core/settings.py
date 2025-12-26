from pydantic_settings import BaseSettings


class IPSettings(BaseSettings):
    IP_API_URL: str = "http://ip-api.com/json/{ip}"  # noqa
    IP_API_TIMEOUT: float = 10.0  # seconds


API_V1_PREFIX = "/api/v1"
