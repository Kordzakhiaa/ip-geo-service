from ipaddress import IPv4Address, ip_address


def validate_ipv4(ip: str) -> bool:
    try:
        return isinstance(ip_address(ip), IPv4Address)
    except ValueError:
        return False
