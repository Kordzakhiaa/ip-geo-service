import pytest

from app.utils.validators import validate_ipv4


@pytest.mark.parametrize(
    "ip, expected",
    [
        ("0.0.0.0", True),
        ("255.255.255.255", True),
        ("192.168.1", False),
        ("192.168.1.1.1", False),
        ("01.2.3.4", False),
        ("256.1.1.1", False),
        ("-1.2.3.4", False),
        ("a.b.c.d", False),
        ("192.168.1.1 ", False),
        ("192.168.1.1/24", False),
        ("", False),
    ],
)
def test_ipv4_edge_cases(ip, expected):
    assert validate_ipv4(ip) == expected
