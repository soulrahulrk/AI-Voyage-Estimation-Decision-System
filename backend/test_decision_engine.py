"""
Unit tests for the decision engine.
Run with: pytest backend/test_decision_engine.py -v
"""

import pytest
from backend.decision_engine import decide_voyage, PROFIT_HIGH_THRESH, FUEL_DOMINANT_THRESH


def test_high_profit_with_high_fuel_should_downgrade_to_caution():
    """
    Test Case 1: High profit (65%) + High fuel (80%) → STRONG GO downgraded to GO WITH CAUTION
    This is the main bug fix scenario.
    """
    # Scenario from the bug report
    total_expense = 496_523.81
    profit = 323_476.19
    fuel_cost = 401_523.81
    port_charges = 95_000.0
    speed_knots = 14.0
    
    result = decide_voyage(profit, total_expense, fuel_cost, port_charges, speed_knots)
    
    # Assertions
    assert result["profit_zone"] == "HIGH", "Should be HIGH profit zone (65% > 15%)"
    assert result["decision"] == "GO WITH CAUTION", "Should downgrade from STRONG GO to GO WITH CAUTION due to fuel dominance"
    assert "FUEL_DOMINANT" in result["risk_flags"], "Should flag fuel dominance"
    assert result["decision"] != "DO NOT SAIL", "MUST NOT be DO NOT SAIL when profit is positive and strong"
    assert result["fuel_percent_of_expense"] > FUEL_DOMINANT_THRESH, "Fuel should be > 60%"
    assert len(result["suggestions"]) > 0, "Should provide actionable suggestions"


def test_negative_profit_should_be_do_not_sail():
    """
    Test Case 2: Negative profit → DO NOT SAIL (only valid scenario for DO NOT SAIL)
    """
    total_expense = 500_000.0
    profit = -50_000.0  # Loss
    fuel_cost = 300_000.0
    port_charges = 200_000.0
    
    result = decide_voyage(profit, total_expense, fuel_cost, port_charges)
    
    assert result["profit_zone"] == "LOSS"
    assert result["decision"] == "DO NOT SAIL"
    assert "Voyage loss expected" in result["risk_flags"]
    assert any("loss-making" in s.lower() for s in result["suggestions"])


def test_low_margin_should_be_risky():
    """
    Test Case 3: Low profit margin (1-3%) → RISKY + LOW_MARGIN flag
    """
    total_expense = 500_000.0
    profit = 15_000.0  # 3% profit
    fuel_cost = 300_000.0
    port_charges = 200_000.0
    
    result = decide_voyage(profit, total_expense, fuel_cost, port_charges)
    
    assert result["profit_zone"] == "LOW"
    assert result["decision"] == "RISKY"
    assert "LOW_MARGIN" in result["risk_flags"]
    assert result["profit_percent"] < 5.0


def test_invalid_input_should_be_manual_review():
    """
    Test Case 4: Invalid inputs (total_expense <= 0) → MANUAL_REVIEW
    """
    total_expense = 0.0  # Invalid
    profit = 100_000.0
    fuel_cost = 0.0
    port_charges = 0.0
    
    result = decide_voyage(profit, total_expense, fuel_cost, port_charges)
    
    assert result["decision"] == "MANUAL_REVIEW"
    assert "INVALID_INPUT" in result["risk_flags"]
    assert any("invalid" in s.lower() for s in result["suggestions"])


def test_medium_profit_with_normal_fuel_should_be_go_with_caution():
    """
    Test Case 5: Medium profit (10%) + Normal fuel (50%) → GO WITH CAUTION
    """
    total_expense = 400_000.0
    profit = 40_000.0  # 10% profit
    fuel_cost = 200_000.0  # 50% fuel
    port_charges = 200_000.0
    
    result = decide_voyage(profit, total_expense, fuel_cost, port_charges)
    
    assert result["profit_zone"] == "MEDIUM"
    assert result["decision"] == "GO WITH CAUTION"
    assert result["fuel_percent_of_expense"] < FUEL_DOMINANT_THRESH
    assert "FUEL_DOMINANT" not in result["risk_flags"]


def test_high_profit_low_fuel_should_be_strong_go():
    """
    Test Case 6: High profit (25%) + Low fuel (40%) + Low port (10%) → STRONG GO (no downgrade)
    """
    # Set up scenario where fuel < 60% and port < 20%
    total_expense = 500_000.0
    profit = 125_000.0  # 25% profit (HIGH zone)
    fuel_cost = 200_000.0  # 40% of expense (below 60% threshold)
    port_charges = 50_000.0  # 10% of expense (below 20% threshold)
    # Remaining 250k could be other costs, but we only track fuel+port
    
    result = decide_voyage(profit, total_expense, fuel_cost, port_charges)
    
    assert result["profit_zone"] == "HIGH"
    assert result["decision"] == "STRONG GO", "Should be STRONG GO with low fuel and port percentages"
    assert result["fuel_percent_of_expense"] < 60.0, "Fuel should be below 60%"
    assert result["port_percent_of_expense"] < 20.0, "Port should be below 20%"
    assert "FUEL_DOMINANT" not in result["risk_flags"]
    assert "PORT_HEAVY_ROUTE" not in result["risk_flags"]


def test_port_heavy_route_should_downgrade():
    """
    Test Case 7: High profit + Port-heavy (25%) → downgrade to GO WITH CAUTION
    """
    total_expense = 400_000.0
    profit = 80_000.0  # 20% profit (HIGH)
    fuel_cost = 200_000.0  # 50% fuel
    port_charges = 200_000.0  # 50% port (> 20% threshold)
    
    result = decide_voyage(profit, total_expense, fuel_cost, port_charges)
    
    assert result["profit_zone"] == "HIGH"
    assert result["decision"] == "GO WITH CAUTION"  # Downgraded due to fuel AND port
    assert "PORT_HEAVY_ROUTE" in result["risk_flags"]


def test_high_speed_warning():
    """
    Test Case 8: High speed (>18 knots) → HIGH_SPEED_FUEL_BURN flag
    """
    total_expense = 400_000.0
    profit = 80_000.0
    fuel_cost = 200_000.0
    port_charges = 200_000.0
    speed_knots = 22.0  # High speed
    
    result = decide_voyage(profit, total_expense, fuel_cost, port_charges, speed_knots)
    
    assert "HIGH_SPEED_FUEL_BURN" in result["risk_flags"]
    assert any("slow steaming" in s.lower() for s in result["suggestions"])


def test_exact_bug_scenario():
    """
    Exact scenario from the bug report to ensure fix works.
    """
    # Inputs from bug report
    distance = 6200  # nm
    speed = 14  # knots
    fuel_consumption = 32  # tons/day
    fuel_price = 680  # $/ton
    port_charges = 95_000
    freight_income = 820_000
    
    # Calculate voyage metrics (as done in fuel_tool and main)
    voyage_days = distance / (speed * 24)
    total_fuel_used = fuel_consumption * voyage_days
    fuel_cost = total_fuel_used * fuel_price
    total_expense = fuel_cost + port_charges
    profit = freight_income - total_expense
    
    result = decide_voyage(profit, total_expense, fuel_cost, port_charges, speed)
    
    # Expected outputs from bug report
    assert result["profit_zone"] == "HIGH"
    assert result["decision"] in ["STRONG GO", "GO WITH CAUTION"], \
        f"Should be STRONG GO or GO WITH CAUTION, not {result['decision']}"
    assert result["decision"] != "DO NOT SAIL", "MUST NOT be DO NOT SAIL for profitable voyage"
    assert "FUEL_DOMINANT" in result["risk_flags"]
    assert result["fuel_percent_of_expense"] > 60.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
