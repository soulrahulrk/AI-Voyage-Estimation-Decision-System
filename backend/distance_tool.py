"""
Distance calculation tool using predefined realistic routes.
"""

from typing import Dict


class DistanceToolFailure(Exception):
    """Raised when the distance lookup fails."""


def _route_key(start_port: str, end_port: str) -> str:
    return f"{start_port.strip().lower()}->{end_port.strip().lower()}"


# Distances in nautical miles between common routes (illustrative but realistic)
DISTANCE_MAP: Dict[str, float] = {
    _route_key("Singapore", "Shanghai"): 2450,
    _route_key("Singapore", "Mumbai"): 1920,
    _route_key("Singapore", "Rotterdam"): 9800,
    _route_key("Shanghai", "Los Angeles"): 5600,
    _route_key("Shanghai", "Seattle"): 4800,
    _route_key("New York", "Rotterdam"): 3600,
    _route_key("New York", "Hamburg"): 3700,
    _route_key("Houston", "Rotterdam"): 4700,
    _route_key("Houston", "Antwerp"): 4800,
    _route_key("Tokyo", "Vancouver"): 4200,
    _route_key("Tokyo", "Los Angeles"): 4700,
    _route_key("Sydney", "Singapore"): 3800,
    _route_key("Cape Town", "Singapore"): 6000,
    _route_key("Dubai", "Rotterdam"): 7000,
    _route_key("Dubai", "Mumbai"): 1200,
    _route_key("Santos", "Houston"): 4900,
    _route_key("Santos", "Rotterdam"): 5800,
    _route_key("Busan", "Long Beach"): 5500,
}


def calculate_distance(start_port: str, end_port: str) -> float:
    key = _route_key(start_port, end_port)
    if key not in DISTANCE_MAP:
        raise DistanceToolFailure("Distance Tool Failure")
    return DISTANCE_MAP[key]
