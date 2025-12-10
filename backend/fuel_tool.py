"""
Fuel and cost calculation tool.
"""

from typing import Tuple


class FuelToolFailure(Exception):
    """Raised when the fuel tool cannot complete."""


def calculate_fuel_and_cost(distance_nm: float, speed_knots: float, consumption_tpd: float, fuel_price_per_ton: float) -> Tuple[float, float, float]:
    """
    Returns voyage_days, total_fuel_used, total_fuel_cost.
    Speed is in knots (nautical miles per hour); consumption in tons per day.
    """
    if speed_knots <= 0 or consumption_tpd <= 0 or fuel_price_per_ton <= 0:
        raise FuelToolFailure("Fuel Tool Failure")

    # Voyage days based on knots -> nm/hour -> hours -> days
    voyage_days = distance_nm / (speed_knots * 24)
    total_fuel_used = consumption_tpd * voyage_days
    total_fuel_cost = total_fuel_used * fuel_price_per_ton
    return voyage_days, total_fuel_used, total_fuel_cost
