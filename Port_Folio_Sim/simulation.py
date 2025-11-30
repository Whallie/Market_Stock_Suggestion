# simulation.py
import random
import math
from typing import Dict, List
from constants import ASSET_PROFILES, DEFAULT_MAX_YEARS


def percentile(sorted_list: List[float], p: float) -> float:
    if not sorted_list:
        return 0.0
    k = (len(sorted_list) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(sorted_list[int(k)])
    d0 = sorted_list[int(f)] * (c - k)
    d1 = sorted_list[int(c)] * (k - f)
    return float(d0 + d1)


def simulate_one_path(
    allocation: Dict[str, float],
    initial_amount_by_asset: Dict[str, float],
    annual_contribution_by_asset: Dict[str, float],
    years: int
) -> Dict[str, List[float]]:

    balances = {asset: [initial_amount_by_asset.get(asset, 0.0)] for asset in allocation.keys()}

    for y in range(1, years + 1):
        for asset in allocation.keys():

            prev = balances[asset][-1]
            mean = ASSET_PROFILES[asset]["mean"]
            vol = ASSET_PROFILES[asset]["vol"]

            # Random simulated return
            r = random.gauss(mean, vol)

            new_balance = prev * (1 + r) + annual_contribution_by_asset.get(asset, 0.0)
            balances[asset].append(max(new_balance, 0.0))

    return balances


def run_monte_carlo(
    allocation: Dict[str, float],
    investable_balance: float,
    annual_contribution: float,
    years: int,
    simulations: int
):

    initial_by_asset = {asset: investable_balance * pct for asset, pct in allocation.items()}
    annual_contrib_by_asset = {asset: annual_contribution * pct for asset, pct in allocation.items()}

    # portfolio totals for each year
    portfolio_totals_per_year = [[] for _ in range(years + 1)]

    for _ in range(simulations):
        path = simulate_one_path(allocation, initial_by_asset, annual_contrib_by_asset, years)
        for y in range(years + 1):
            total = sum(path[asset][y] for asset in allocation.keys())
            portfolio_totals_per_year[y].append(total)

    # percentiles
    portfolio_percentiles = []
    for y in range(years + 1):
        arr = sorted(portfolio_totals_per_year[y])
        p10 = percentile(arr, 10)
        p50 = percentile(arr, 50)
        p90 = percentile(arr, 90)
        portfolio_percentiles.append({
            "year": y,
            "p10": round(p10, 2),
            "p50": round(p50, 2),
            "p90": round(p90, 2)
        })

    # per-asset median helper sims
    helper_sims = max(100, int(simulations * 0.05))
    per_asset_aggregator = {asset: [[] for _ in range(years + 1)] for asset in allocation.keys()}

    for _ in range(helper_sims):
        path = simulate_one_path(allocation, initial_by_asset, annual_contrib_by_asset, years)
        for asset in allocation.keys():
            for y in range(years + 1):
                per_asset_aggregator[asset][y].append(path[asset][y])

    per_asset_median_series = {}
    for asset in allocation.keys():
        median_series = []
        for y in range(years + 1):
            arr = sorted(per_asset_aggregator[asset][y])
            m = percentile(arr, 50)
            median_series.append({"year": y, "median": round(m, 2)})
        per_asset_median_series[asset] = median_series

    return {
        "portfolio_percentiles": portfolio_percentiles,
        "per_asset_medians": per_asset_median_series,
        "simulations_used": simulations
    }


def years_to_reach_real_target(
    initial_investable: float,
    annual_contribution: float,
    assumed_annual_return: float,
    inflation_rate: float,
    target_present_value: float,
    max_years: int = DEFAULT_MAX_YEARS
):
    balance = initial_investable
    for year in range(0, max_years + 1):
        denom = (1 + inflation_rate) ** year
        real_balance = balance / denom

        if real_balance >= target_present_value:
            return year, real_balance

        balance = balance * (1 + assumed_annual_return) + annual_contribution

    return None, real_balance
