"""
Decision engine for voyage profitability.
"""

from typing import Dict, List


class DecisionEngineFailure(Exception):
    """Raised when the decision engine cannot complete."""


PROFIT_ZONES: Dict[str, tuple[float, float]] = {
    "STRONG GO": (15, float("inf")),
    "GO WITH CAUTION": (5, 15),
    "RISKY": (0, 5),
    "DO NOT SAIL": (float("-inf"), 0),
}


def classify_profit_zone(profit_percent: float) -> str:
    for zone, (low, high) in PROFIT_ZONES.items():
        if low <= profit_percent < high:
            return zone
    return "DO NOT SAIL"


def decision_engine(
    fuel_cost: float,
    port_charges: float,
    freight_income: float,
    speed_knots: float,
) -> Dict[str, object]:
    if fuel_cost < 0 or port_charges < 0 or freight_income <= 0:
        raise DecisionEngineFailure("Decision Engine Failure")

    expense = fuel_cost + port_charges
    # Avoid division by zero; treat zero expense as needing manual review
    if expense <= 0:
        raise DecisionEngineFailure("Decision Engine Failure")

    net_profit = freight_income - expense
    profit_percent = (net_profit / expense) * 100

    profit_zone = classify_profit_zone(profit_percent)
    fuel_pct = (fuel_cost / expense) * 100
    port_pct = (port_charges / expense) * 100

    decision = profit_zone
    suggestions: List[str] = []
    risk_flags: List[str] = []

    if net_profit < 0:
        decision = "DO NOT SAIL"
        risk_flags.append("Voyage loss expected")
    if fuel_cost > 0.75 * expense:
        decision = "DO NOT SAIL"
        risk_flags.append("Fuel cost dominates (>75% of expense)")
        suggestions.append("Renegotiate freight or adjust fuel plan")
    elif fuel_cost > 0.65 * expense:
        risk_flags.append("Fuel heavy voyage (>65% of expense)")
    if speed_knots > 18:
        risk_flags.append("High speed warning: fuel burn elevated")
    if port_charges > 0.20 * expense:
        risk_flags.append("Port charges heavy (>20% of expense)")
    if freight_income < fuel_cost:
        risk_flags.append("Freight below fuel cost")
        suggestions.append("Renegotiate freight rate or adjust speed")

    if decision == "DO NOT SAIL" and "Renegotiate freight or adjust fuel plan" not in suggestions:
        suggestions.append("Revisit commercial terms or routing")
    if decision.startswith("GO") and fuel_pct > 60:
        suggestions.append("Monitor bunker market and consider slow steaming")
    if net_profit > 0 and profit_percent < 10:
        suggestions.append("Seek additional cargo or adjust port calls")

    return {
        "net_profit": net_profit,
        "profit_percent": profit_percent,
        "profit_zone": profit_zone,
        "fuel_percent_of_expense": fuel_pct,
        "port_percent_of_expense": port_pct,
        "decision": decision,
        "suggestions": suggestions,
        "risk_flags": risk_flags,
    }
