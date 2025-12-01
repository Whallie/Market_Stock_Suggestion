import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
from pprint import pprint
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE_DIR, "..", "data", "Checked_Stock_Inds.csv")
df_tk = pd.read_csv(csv_path, dtype=str)
cant_cal = ['S&J', 'WELL', 'ACAP', 'MNIT', 'TAPAC', 'TIF1', 'MANRIN']

fail = []

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
def forecast_stock_prices(years_forecast, n_sims=5000):
    if years_forecast <= 0:
        return {"Error": "Years forecast must be greater than 0."}
    
    yst = datetime.now().year - years_forecast
    start = f"{str(yst)}-01-01"
    end = datetime.today().strftime('%Y-%m-%d')

    res = {}

    for index, row in df_tk.iterrows():
        now_tk = []
        cnt = 0
        for cols in df_tk.columns:
            cnt += 1
            if (cnt >= 2 and pd.isna(df_tk.iloc[index, cnt-1]) == False):
                if (str(df_tk.iloc[index, cnt-1]) in cant_cal):
                    continue
                now_tk.append(str(df_tk.iloc[index, cnt-1])+".BK")
            elif (cnt >= 2):
                break

        df_now = pd.DataFrame()
        for t in now_tk:
            df_daily = yf.download(t, start=start, end=end, interval="1d", auto_adjust=True, progress=True)
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

            if (price_daily.index[0].year != pd.to_datetime(start).year):
                continue

            price_monthly = price_daily.resample('ME').last().dropna()
            price_monthly = price_monthly.rename(columns={price_monthly.columns[0]: "Value"})
            now_so = yf.Ticker(t).info['sharesOutstanding']
            now_fs = yf.Ticker(t).info['floatShares']
            now_ff = now_fs/now_so
            price_monthly['Value'] = price_monthly['Value']*now_so*now_ff
            if (df_now.empty):
                df_now = price_monthly.copy()
                continue
            df_now = df_now.add(price_monthly, fill_value=0)

        BMV = df_now.iloc[0]['Value']
        df_now['Value'] = (df_now['Value']/BMV)*100.0
        # print(df_now.head)
        log_returns_monthly = np.log(df_now / df_now.shift(1)).dropna()
        mu_y = float(log_returns_monthly.mean()) * 12.0
        sigma_y = float(log_returns_monthly.std(ddof=1)) * np.sqrt(12.0)
        S0 = df_now.iloc[-1]
        paths = monte_carlo_gbm_monthly(S0, mu_y, sigma_y, years_forecast, n_sims=n_sims)
        S0 = float(S0)
        last_price = paths[-1, :]

        median = np.median(last_price)
        mean = np.mean(last_price)
        prob_gain = np.mean(last_price >= S0)
        
        indus = df_tk.iloc[index, 0]

        if np.isnan(median) or np.isnan(mean) or prob_gain == 0:
            fail.append(indus)
            continue
        
        res[indus] = {
            "Name": indus,
            "start_price": float(S0),
            "median": float(median),
            "mean": float(mean),
            "prob_gain": float(prob_gain),
            "prob_loss": 1.0-float(prob_gain)
        }

    return res
#----------------------------------------------------------------------------------#

# For testing
# pprint(forecast_stock_prices(5))
# print("fail:", fail)