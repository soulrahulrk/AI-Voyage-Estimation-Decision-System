"""
Decision engine for voyage profitability.
Implements rule-based decision logic with profit zones and risk assessment.
"""

from typing import Dict, List, Optional


class DecisionEngineFailure(Exception):
    """Raised when the decision engine cannot complete."""


# Decision thresholds (configurable constants)
PROFIT_HIGH_THRESH = 15.0  # >= 15% = HIGH profit zone
PROFIT_MEDIUM_THRESH = 5.0  # 5-15% = MEDIUM profit zone
FUEL_DOMINANT_THRESH = 60.0  # > 60% = fuel dominates expense
PORT_HEAVY_THRESH = 20.0  # > 20% = port-heavy route
HIGH_SPEED_THRESH = 18.0  # > 18 knots = high fuel burn warning


def decide_voyage(
    profit: float,
    total_expense: float,
    fuel_cost: float,
    port_charges: float,
    speed_knots: Optional[float] = None,
) -> Dict[str, object]:
    """
    Core decision engine for voyage profitability and risk assessment.
    
    Args:
        profit: Net profit (Freight Income - Total Expense)
        total_expense: Total voyage expense (Fuel Cost + Port Charges)
        fuel_cost: Total fuel cost
        port_charges: Total port charges
        speed_knots: Optional vessel speed for high-speed warnings
    
    Returns:
        Dictionary with profit_zone, final_decision, risk_flags, suggestions, and percentages
    """
    suggestions: List[str] = []
    risk_flags: List[str] = []
    
    # Handle invalid inputs
    if total_expense <= 0 or profit is None or fuel_cost < 0 or port_charges < 0:
        return {
            "net_profit": profit,
            "profit_percent": 0.0,
            "profit_zone": "LOSS",
            "fuel_percent_of_expense": 0.0,
            "port_percent_of_expense": 0.0,
            "decision": "MANUAL_REVIEW",
            "suggestions": ["Inputs invalid or incomplete. Please review voyage parameters."],
            "risk_flags": ["INVALID_INPUT"],
        }
    
    # Calculate percentages
    profit_pct = (profit / total_expense) * 100
    fuel_pct = (fuel_cost / total_expense) * 100
    port_pct = (port_charges / total_expense) * 100
    
    # Step 1: Determine profit zone based on profit percentage
    if profit < 0:
        profit_zone = "LOSS"
    elif profit_pct >= PROFIT_HIGH_THRESH:
        profit_zone = "HIGH"
    elif profit_pct >= PROFIT_MEDIUM_THRESH:
        profit_zone = "MEDIUM"
    else:
        profit_zone = "LOW"
    
    # Step 2: Determine base decision from profit zone
    if profit < 0:
        final_decision = "DO NOT SAIL"
        risk_flags.append("Voyage loss expected")
        suggestions.append("Cancel or renegotiate this voyage; it is currently loss-making.")
    else:
        # Profit >= 0, determine base decision
        if profit_zone == "HIGH":
            final_decision = "STRONG GO"
        elif profit_zone == "MEDIUM":
            final_decision = "GO WITH CAUTION"
        else:  # LOW
            final_decision = "RISKY"
            risk_flags.append("LOW_MARGIN")
            suggestions.append("Negotiate higher freight or reduce costs; margin is too thin.")
        
        # Step 3: Apply risk rules (downgrades only, never to DO NOT SAIL unless profit < 0)
        
        # Rule 1: Fuel dominance (> 60%)
        if fuel_pct > FUEL_DOMINANT_THRESH:
            risk_flags.append("FUEL_DOMINANT")
            suggestions.append("Reduce speed or improve fuel plan to lower fuel share of expense.")
            
            # Downgrade STRONG GO → GO WITH CAUTION
            if final_decision == "STRONG GO":
                final_decision = "GO WITH CAUTION"
        
        # Rule 2: Port-heavy route (> 20%)
        if port_pct > PORT_HEAVY_THRESH:
            risk_flags.append("PORT_HEAVY_ROUTE")
            suggestions.append("Consider alternate port or negotiate lower port charges.")
            
            # Downgrade STRONG GO → GO WITH CAUTION
            if final_decision == "STRONG GO":
                final_decision = "GO WITH CAUTION"
        
        # Rule 3: High speed warning (> 18 knots)
        if speed_knots and speed_knots > HIGH_SPEED_THRESH:
            risk_flags.append("HIGH_SPEED_FUEL_BURN")
            suggestions.append("High speed detected; consider slow steaming to reduce fuel costs.")
    
    return {
        "net_profit": profit,
        "profit_percent": profit_pct,
        "profit_zone": profit_zone,
        "fuel_percent_of_expense": fuel_pct,
        "port_percent_of_expense": port_pct,
        "decision": final_decision,
        "suggestions": suggestions,
        "risk_flags": risk_flags,
    }


def decision_engine(
    fuel_cost: float,
    port_charges: float,
    freight_income: float,
    speed_knots: float,
) -> Dict[str, object]:
    """
    Legacy wrapper for decide_voyage to maintain API compatibility.
    Calculates profit and total expense, then calls decide_voyage.
    """
    if fuel_cost < 0 or port_charges < 0 or freight_income <= 0:
        raise DecisionEngineFailure("Decision Engine Failure")
    
    total_expense = fuel_cost + port_charges
    
    if total_expense <= 0:
        raise DecisionEngineFailure("Decision Engine Failure")
    
    profit = freight_income - total_expense
    
    return decide_voyage(profit, total_expense, fuel_cost, port_charges, speed_knots)
