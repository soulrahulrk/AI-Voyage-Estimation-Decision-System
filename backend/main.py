"""
AI Voyage Estimation & Decision System backend.
Run with: uvicorn backend.main:app --reload
"""

from typing import Any, Callable, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from .distance_tool import DistanceToolFailure, calculate_distance
from .fuel_tool import FuelToolFailure, calculate_fuel_and_cost
from .decision_engine import DecisionEngineFailure, decision_engine

app = FastAPI(title="AI Voyage Estimation & Decision System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class VoyageRequest(BaseModel):
    start_port: str = Field(..., description="Start Port")
    end_port: str = Field(..., description="End Port")
    speed: float = Field(..., description="Speed in knots")
    fuel_consumption: float = Field(..., description="Fuel consumption in tons/day")
    fuel_price: float = Field(..., description="Fuel price per ton")
    port_charges: float = Field(..., description="Port charges")
    freight_income: float = Field(..., description="Freight income")
    currency: str = Field(..., pattern="^(USD|INR|EUR)$")
    manual_distance: Optional[float] = None
    manual_fuel_cost: Optional[float] = None

    @field_validator("start_port", "end_port")
    @classmethod
    def non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field is required")
        return v

    @field_validator(
        "speed",
        "fuel_consumption",
        "fuel_price",
        "port_charges",
        "freight_income",
    )
    @classmethod
    def non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Negative values are not allowed")
        return v

    @field_validator("fuel_price")
    @classmethod
    def fuel_price_non_zero(cls, v: float) -> float:
        if v == 0:
            raise ValueError("Fuel price cannot be zero")
        return v


class VoyageResponse(BaseModel):
    distance_nm: Optional[float]
    voyage_days: Optional[float]
    total_fuel_used: Optional[float]
    total_fuel_cost: Optional[float]
    total_expense: Optional[float]
    net_profit: Optional[float]
    profit_percent: Optional[float]
    profit_zone: Optional[str]
    fuel_percent_of_expense: Optional[float]
    port_percent_of_expense: Optional[float]
    final_decision: str
    suggestions: List[str]
    risk_flags: List[str]
    warnings: List[str]
    banners: List[str]
    needs_manual_distance: bool = False
    needs_manual_fuel_cost: bool = False
    currency: str


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


def run_with_retry(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    try:
        return func(*args, **kwargs)
    except Exception:
        return func(*args, **kwargs)


@app.post("/estimate", response_model=VoyageResponse)
def estimate_voyage(payload: VoyageRequest):
    warnings: List[str] = []
    risk_flags: List[str] = []
    banners: List[str] = []

    if payload.speed > 20:
        warnings.append("Speed exceeds 20 knots: fuel burn warning")
    if payload.freight_income < 50000:
        warnings.append("Freight below $50,000: commercial warning")

    # Distance phase
    distance_nm: Optional[float] = None
    needs_manual_distance = False
    try:
        distance_nm = run_with_retry(calculate_distance, payload.start_port, payload.end_port)
    except DistanceToolFailure:
        if payload.manual_distance and payload.manual_distance > 0:
            distance_nm = payload.manual_distance
            warnings.append("Used manual distance input")
        else:
            needs_manual_distance = True
            banners.append("Distance tool failed. Provide manual distance to continue.")

    if needs_manual_distance:
        return VoyageResponse(
            distance_nm=None,
            voyage_days=None,
            total_fuel_used=None,
            total_fuel_cost=None,
            total_expense=None,
            net_profit=None,
            profit_percent=None,
            profit_zone=None,
            fuel_percent_of_expense=None,
            port_percent_of_expense=None,
            final_decision="MANUAL INPUT REQUIRED",
            suggestions=["Enter distance manually and resubmit"],
            risk_flags=risk_flags,
            warnings=warnings,
            banners=banners,
            needs_manual_distance=True,
            needs_manual_fuel_cost=False,
            currency=payload.currency,
        )

    # Fuel phase
    voyage_days: Optional[float] = None
    total_fuel_used: Optional[float] = None
    total_fuel_cost: Optional[float] = None
    needs_manual_fuel_cost = False
    try:
        voyage_days, total_fuel_used, total_fuel_cost = run_with_retry(
            calculate_fuel_and_cost,
            distance_nm,
            payload.speed,
            payload.fuel_consumption,
            payload.fuel_price,
        )
    except FuelToolFailure:
        if payload.manual_fuel_cost and payload.manual_fuel_cost > 0:
            total_fuel_cost = payload.manual_fuel_cost
            warnings.append("Used manual fuel cost input")
            if distance_nm is not None and payload.speed > 0:
                voyage_days = distance_nm / (payload.speed * 24)
                total_fuel_used = payload.fuel_consumption * voyage_days
        else:
            needs_manual_fuel_cost = True
            banners.append("Fuel tool failed. Provide manual fuel cost to continue.")

    if needs_manual_fuel_cost:
        return VoyageResponse(
            distance_nm=distance_nm,
            voyage_days=voyage_days,
            total_fuel_used=total_fuel_used,
            total_fuel_cost=None,
            total_expense=None,
            net_profit=None,
            profit_percent=None,
            profit_zone=None,
            fuel_percent_of_expense=None,
            port_percent_of_expense=None,
            final_decision="MANUAL INPUT REQUIRED",
            suggestions=["Enter fuel cost manually and resubmit"],
            risk_flags=risk_flags,
            warnings=warnings,
            banners=banners,
            needs_manual_distance=False,
            needs_manual_fuel_cost=True,
            currency=payload.currency,
        )

    # Decision phase
    total_expense = None
    net_profit = None
    profit_percent = None
    profit_zone = None
    fuel_pct = None
    port_pct = None
    final_decision = "MANUAL REVIEW REQUIRED"
    suggestions: List[str] = []

    try:
        decision_result = run_with_retry(
            decision_engine,
            total_fuel_cost,
            payload.port_charges,
            payload.freight_income,
            payload.speed,
        )
        net_profit = float(decision_result["net_profit"])
        profit_percent = float(decision_result["profit_percent"])
        profit_zone = str(decision_result["profit_zone"])
        fuel_pct = float(decision_result["fuel_percent_of_expense"])
        port_pct = float(decision_result["port_percent_of_expense"])
        final_decision = str(decision_result["decision"])
        suggestions = list(decision_result["suggestions"])
        risk_flags.extend(list(decision_result["risk_flags"]))
    except DecisionEngineFailure:
        banners.append("Decision engine offline. Manual review required.")
        final_decision = "MANUAL REVIEW REQUIRED"

    total_expense = (total_fuel_cost or 0) + payload.port_charges
    if net_profit is None:
        net_profit = payload.freight_income - total_expense if total_expense else None
    if profit_percent is None and total_expense:
        profit_percent = (net_profit / total_expense) * 100 if net_profit is not None else None
    if profit_zone is None and profit_percent is not None:
        profit_zone = "RISKY" if profit_percent >= 0 else "DO NOT SAIL"
    if fuel_pct is None and total_expense:
        fuel_pct = (total_fuel_cost / total_expense) * 100 if total_fuel_cost is not None else None
    if port_pct is None and total_expense:
        port_pct = (payload.port_charges / total_expense) * 100

    if net_profit is not None and net_profit < 0:
        banners.append("Loss-making voyage detected")
    elif profit_zone == "RISKY":
        banners.append("Risky voyage")

    return VoyageResponse(
        distance_nm=distance_nm,
        voyage_days=voyage_days,
        total_fuel_used=total_fuel_used,
        total_fuel_cost=total_fuel_cost,
        total_expense=total_expense,
        net_profit=net_profit,
        profit_percent=profit_percent,
        profit_zone=profit_zone,
        fuel_percent_of_expense=fuel_pct,
        port_percent_of_expense=port_pct,
        final_decision=final_decision,
        suggestions=suggestions,
        risk_flags=risk_flags,
        warnings=warnings,
        banners=banners,
        needs_manual_distance=False,
        needs_manual_fuel_cost=False,
        currency=payload.currency,
    )
