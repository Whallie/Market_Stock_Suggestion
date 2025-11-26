import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
from pprint import pprint
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE_DIR, "..", "data", "thai_yahoo_symbols.csv")
df_tk = pd.read_csv(csv_path, dtype=str)

tk = [s.strip().upper() for s in df_tk["symbol"].tolist()]
# tk = ["^SET.BK", "^SET50.BK", "^SET100.BK", "^SSET.BK", "^MAI.BK"]

#----------------------------------------------------------------------------------#
def monte_carlo_gbm_monthly(S0, mu_y, sigma_y, years, n_sims=10000):
    months = int(years * 12)
    dt = 1.0 / 12.0
    prices = np.zeros((months + 1, n_sims))
    prices[0, :] = S0
    mu_m = mu_y * dt
    sigma_m = sigma_y * np.sqrt(dt)
    for t in range(1, months + 1):
        z = np.random.normal(size=n_sims)
        prices[t, :] = prices[t-1, :] * np.exp((mu_m - 0.5 * sigma_m**2) + sigma_m * z)
    return prices
#----------------------------------------------------------------------------------#

#----------------------------------------------------------------------------------#
def forecast_stock_prices(years_forecast, n_sims=10000, tickers = tk):
    if years_forecast <= 0:
        return {"Error": "Years forecast must be greater than 0."}
    
    yst = datetime.now().year - 20
    start = f"{str(yst)}-1-1"
    end = datetime.today().strftime('%Y-%m-%d')

    res = {}
    for ticker in tickers:
        res[ticker] = None

    for ticker in tickers:
        df_daily = yf.download(ticker, start=start, end=end, interval="1d", auto_adjust=True, progress=True)
        if len(df_daily) < 2:
            continue
        if "Adj Close" in df_daily.columns:
            price_daily = df_daily["Adj Close"].copy()
        elif "Close" in df_daily.columns:
            price_daily = df_daily["Close"].copy()
        else:
            price_daily = df_daily.iloc[:, 3].copy()

        price_daily = price_daily.dropna()
        price_daily.index = pd.to_datetime(price_daily.index)

        #print(price_daily.head())

        if (price_daily.index[0].year != pd.to_datetime(start).year):
            #print("Latest data is not up-to-date for", price_daily.index[0], "vs", pd.to_datetime(start))
            continue

        price_monthly = price_daily.resample('ME').last().dropna()
        log_returns_monthly = np.log(price_monthly / price_monthly.shift(1)).dropna()
        mu_y = float(log_returns_monthly.mean()) * 12.0
        sigma_y = float(log_returns_monthly.std(ddof=1)) * np.sqrt(12.0)
        S0 = price_monthly.iloc[-1]
        paths = monte_carlo_gbm_monthly(S0, mu_y, sigma_y, years_forecast, n_sims=n_sims)
        S0 = float(S0)
        last_price = paths[-1, :]

        median = np.median(last_price)
        mean = np.mean(last_price)
        prob_gain = np.mean(last_price >= S0)

        if np.isnan(median) or np.isnan(mean) or prob_gain == 0:
            continue
        
        res[ticker] = {
            "start_price": float(S0),
            "median": float(median),
            "mean": float(mean),
            "prob_gain": float(prob_gain)
        }
    return res
#----------------------------------------------------------------------------------#

#pprint(forecast_stock_prices(5))