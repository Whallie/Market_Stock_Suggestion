from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from app import MS_FC as ms
import numpy as np
import pandas as pd
import math as ma
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE_DIR, "..", "data", "Market_Stock_List.csv")
df_market = pd.read_csv(csv_path, dtype=str)

app = FastAPI()

class user_data(BaseModel):
    all_money : float = 0.0
    income : float = 0.0
    income_freq : int = 0 # amount of income times per year
    expense: float = 0.0 # per month
    saving_cost : float = 0.0
    saving_freq : int = 0 # amount of saving times per year
    saving_now : float = 0.0
    saving_interest : float = 0.0 # yearly interest rate in percentage
    goal_years: int = 0
    goal_price : float = 0.0 # DO NOT consider inflation here
    risk_lv : int = 1 # 1 to 5: 90 70 50 30 10 percent of risk 
    emergency : float = 0.0 # money that won't be used for investment (must <= all_money)

@app.post("/market_stock/suggestion")

def make_suggest(data: user_data):
    res = {}

    if data.goal_years <= 0:
        return {"Error": "Years forecast must be greater than 0."}

    market_price = ms.forecast_stock_prices(data.goal_years)
    if not isinstance(market_price, dict):
        return {"Error": "market_price returned unexpected format."}

    years = int(data.goal_years)
    inflation_rate = 0.02 # assumed constant inflation rate of 2%
    # Note: emergency buffer is money that will not be used for investment
    # Emergency buffer cannot exceed all available money
    emergency_buffer = data.emergency if (data.emergency <= data.all_money) else data.all_money
    r_s = float(data.saving_interest) / 100.0 

    user_min_prob = float(20*(6-data.risk_lv)-10) / 100.0

    annual_income = data.income * data.income_freq
    annual_expense = data.expense * 12.0
    planned_saving_per_year = data.saving_cost * data.saving_freq

    surplus_per_year = annual_income - annual_expense - planned_saving_per_year
    if surplus_per_year < 0:
        return {"Error": "Saving plan is not possible: expenses + planned savings exceed income."}


    available_from_saving_now = max(0.0, data.saving_now - emergency_buffer)
    emergency_buffer -= (data.saving_now - available_from_saving_now)
    available_now = max(0.0, data.all_money - data.saving_now - emergency_buffer)
    emergency_buffer = data.emergency if (data.emergency <= data.all_money) else data.all_money

    adj_goal_price = data.goal_price * ((1.0 + inflation_rate) ** years)

    if adj_goal_price <= 0.0:
        return {"Error": "Goal price must be greater than 0."}

    # 1) Money if NOT investing (savings account outcome)
    # Note: assume that the money that does nothing always goes to savings account

    fv_saving_now = data.saving_now * ((1.0 + r_s) ** years)
    now_not_saved = data.all_money - data.saving_now
    fv_saving_now += now_not_saved * ((1.0 + r_s) ** years)

    if abs(r_s) < 1e-12:
        fv_planned_savings = planned_saving_per_year * years
        fv_surplus_savings = surplus_per_year * years
    else:
        ann = ((1.0 + r_s) ** years - 1.0) / r_s
        fv_planned_savings = planned_saving_per_year * ann
        fv_surplus_savings = surplus_per_year * ann

    fv_total_savings = fv_saving_now + fv_planned_savings + fv_surplus_savings

    no_investment = {
        "fv_saving_now": fv_saving_now,
        "fv_planned_savings": fv_planned_savings,
        "fv_surplus_savings": fv_surplus_savings,
        "fv_total_savings": fv_total_savings,
        "pct_goal_covered": float(min(1.0, fv_total_savings / adj_goal_price)) if adj_goal_price > 0 else 0.0
    }

    # 2) For each stock: compute investment plan (lump-sum today + annual contributions from surplus)
    # Note: assume that user will invest with every avalilable, and the money that does nothing always goes to savings account

    stock_results = []

    for sym, info in (market_price.items() if isinstance(market_price, dict) else []):
        if not info:
            continue

        start_price = float(info.get("start_price"))
        median_price = float(info.get("median"))
        mean_price = float(info.get("mean"))
        prob_gain = float(info.get("prob_gain"))

        if mean_price <= start_price:
            continue

        start_price = float(start_price)
        median_price = float(median_price)
        prob_gain = float(prob_gain)

        if years <= 0 or start_price <= 0:
            continue

        R_total = median_price / start_price
        if median_price <= 0:
            annual_return = -1.0
        else:
            if R_total <= 0:
                annual_return = -1.0
            else:
                try:
                    annual_return = R_total ** (1.0 / years) - 1.0
                except Exception:
                    annual_return = -1.0

        if annual_return < 0.0:
            continue

        invest_ann = surplus_per_year
        if invest_ann <= 0:
            fv_invest_ann = 0.0
        else:
            if abs(annual_return) < 1e-12:
                fv_invest_ann = invest_ann * years
            else:
                fv_invest_ann = invest_ann * (((1.0 + annual_return) ** years - 1.0) / annual_return)

        numerator = adj_goal_price - (fv_saving_now + fv_planned_savings) - fv_invest_ann
        gain_no_pull = (fv_saving_now + fv_planned_savings) + fv_invest_ann
        required_lump = max(0.0, numerator / R_total)

        pull_from_avaliable = min(required_lump, available_now)
        remaining_needed = required_lump - pull_from_avaliable
        pull_from_saving = min(remaining_needed, available_from_saving_now)
        rem_now = data.all_money - pull_from_avaliable - pull_from_saving

        fv_rem_saving_now = (rem_now) * ((1.0 + r_s) ** years)

        pull_money_now = min(required_lump, pull_from_avaliable + pull_from_saving)

        fv_lump = pull_money_now * R_total
        fv_invest_total_nominal = (fv_rem_saving_now + fv_planned_savings) + fv_invest_ann + fv_lump

        real_final_today = fv_invest_total_nominal / ((1.0 + inflation_rate) ** years)

        real_profit_today = real_final_today - (pull_from_avaliable + pull_from_saving + surplus_per_year)
        real_profit_at_goal = real_profit_today * ((1.0 + inflation_rate) ** years)

        stock_results.append({
            "Name":  df_market.loc[df_market['Symbol'] == sym[:-3], 'Company'].values[0] if not df_market.loc[df_market['Symbol'] == sym[:-3], 'Company'].empty else "SET Index",
            "start_price": float(start_price),
            "median_price": float(median_price),
            "annual_return": float(annual_return),
            "whole_return": float(R_total),
            "prob_gain": float(prob_gain),
            "below_user_risk": bool((prob_gain >= user_min_prob)),
            "gain_no_pull" : float(gain_no_pull),
            "pct_goal_covered_no_pull": float(min(1.0, gain_no_pull / adj_goal_price))*100.0,
            "required_from_now": float(required_lump),
            "used_from_saving": float(pull_from_avaliable),
            "used_from_other": float(pull_from_saving),
            "gain_with_pull": float(fv_invest_total_nominal),
            "pct_goal_covered_with_pull": float(min(1.0, fv_invest_total_nominal / adj_goal_price))*100.0,
            "ch_profit_today": bool((real_profit_today > 0.0)),
            "ch_profit_at_goal": bool((real_profit_at_goal > 0.0)),
            "real_profit_today": float(real_profit_today),
            "real_profit_at_goal": float(real_profit_at_goal),
        })
        # print("Processed:", sym)

    # 3) Sort and suggest
    allowed = [s for s in stock_results if s["below_user_risk"]]
    upper_risk = [s for s in stock_results if not s["below_user_risk"]]
    upper_risk_sorted = sorted(upper_risk, key=lambda x: (x["prob_gain"], x["real_profit_at_goal"]), reverse=True)
    allowed_sorted = sorted(allowed, key=lambda x: x["real_profit_at_goal"], reverse=True)

    suggestions = []
    suggestions = allowed_sorted[:3] + upper_risk_sorted[:3]

    # Build response
    res["no_investment"] = no_investment
    #res["stock_analysis"] = stock_results
    res["suggestions"] = suggestions
    res["informs"] = {
        "years": years,
        "adj_goal_price": adj_goal_price,
        "user_min_prob": user_min_prob,
        "available_now_total": available_now,
        "available_from_saving_now": available_from_saving_now,
        "emergency_buffer": emergency_buffer
    }

    return res