# app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models import AnalysisRequest
from constants import (
    ALLOCATION_RULES,
    ASSET_PROFILES,
    DEFAULT_MAX_YEARS,
    DEFAULT_MONTE_CARLO_SIMS,
    DISCLAIMER_TEXT
)

from simulation import run_monte_carlo, years_to_reach_real_target

app = FastAPI(title="Portfolio Simulation v2.2 (Educational Demo)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/portfolio/disclaimer")
def get_disclaimer():
    return {"disclaimer": DISCLAIMER_TEXT}


@app.post("/portfolio/analysis")
def analysis(req: AnalysisRequest):
    profile = req.profile

    income = profile.monthly_income
    expense = profile.monthly_expense
    declared_contribution = profile.monthly_contribution
    savings = profile.current_savings
    inflation = profile.inflation_rate
    emergency_amount = profile.emergency_fund_amount
    sims = DEFAULT_MONTE_CARLO_SIMS
    max_years = DEFAULT_MAX_YEARS

    # ======== 1) Calculate spare cash ========
    spare_cash = income - expense

    # Budget check: contribution must not exceed spare cash
    if spare_cash < declared_contribution:
        actual_contribution = max(0, spare_cash)
        budget_note = (
            f"ยอดออมที่ระบุ ({declared_contribution:.2f}/เดือน) "
            f"เกินกำลังจ่ายจริง (เหลือ {spare_cash:.2f}/เดือน). "
            f"ปรับเหลือ {actual_contribution:.2f}/เดือนในการจำลองครั้งนี้"
        )
    else:
        actual_contribution = declared_contribution
        budget_note = None

    # ======== 2) Emergency fund separation ========
    if emergency_amount:
        investable = max(0, savings - emergency_amount)
        shortfall = max(0, emergency_amount - savings)
    else:
        investable = savings
        shortfall = 0

    # ======== 3) readiness ========
    readiness = True
    readiness_notes = []

    if shortfall > 0:
        readiness = False
        readiness_notes.append(f"เงินออมไม่พอสำหรับเงินฉุกเฉิน ต้องมีเพิ่มอีก {shortfall:.2f} บาท")

    if spare_cash <= 0:
        readiness = False
        readiness_notes.append("รายได้ไม่เพียงพอกับรายจ่าย ไม่มีเงินเหลือที่จะออม")

    if budget_note:
        readiness_notes.append(budget_note)

    # ======== 4) Portfolio allocation ========
    rb = profile.risk_bucket.lower() if profile.risk_bucket else "moderate"
    if rb not in ALLOCATION_RULES:
        rb = "moderate"

    allocation = ALLOCATION_RULES[rb]

    annual_contribution = actual_contribution * 12

    # deterministic expected annual return
    est_return = sum(ASSET_PROFILES[a]["mean"] * pct for a, pct in allocation.items())

    # ======== 5) Monte Carlo Simulation ========
    mc = run_monte_carlo(
        allocation=allocation,
        investable_balance=investable,
        annual_contribution=annual_contribution,
        years=max_years,
        simulations=sims
    )

    # ======== 6) Determine time to target (deterministic) ========
    det_years, _ = years_to_reach_real_target(
        initial_investable=investable,
        annual_contribution=annual_contribution,
        assumed_annual_return=est_return,
        inflation_rate=inflation,
        target_present_value=req.target_amount,
        max_years=max_years
    )

    return {
        "disclaimer": DISCLAIMER_TEXT,
        "profile_summary": {
            "monthly_income": income,
            "monthly_expense": expense,
            "monthly_contribution_declared": declared_contribution,
            "monthly_contribution_used": actual_contribution,
            "spare_cash": spare_cash,
            "current_savings": savings,
            "emergency_fund_required": emergency_amount,
            "investable_savings": investable,
            "emergency_shortfall": shortfall,
            "readiness": readiness,
            "readiness_notes": readiness_notes
        },
        "portfolio": {
            "risk_bucket": rb,
            "allocation": allocation,
            "estimated_annual_return": round(est_return, 4),
            "deterministic_years_to_target": det_years,
            "monte_carlo": mc,
            "monte_carlo_sims_used": sims
        }
    }
