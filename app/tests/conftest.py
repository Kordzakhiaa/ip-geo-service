from types import SimpleNamespace
from typing import Any

import pytest

from app.api.v1.endpoints import GeoResponse


@pytest.fixture
def make_request():
    """Return a dummy request object with configurable client IP."""

    def _make(ip: str):
        class DummyRequest:
            client = SimpleNamespace(host=ip)
            headers: dict[Any, Any] = {}

        return DummyRequest()

    return _make


@pytest.fixture
def fake_geo_response():
    """Return a factory for fake GeoResponse objects."""

    def _factory(ip="8.8.8.8", **overrides):
        data = dict(
            ip=ip,
            country="United States",
            region="California",
            city="Mountain View",
            latitude=37.386,
            longitude=-122.0838,
            timezone="America/Los_Angeles",
            isp="Google LLC",
        )
        data.update(overrides)
        return GeoResponse(**data)

    return _factory
