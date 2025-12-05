import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
from pprint import pprint
import os
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE_DIR, "..", "data", "Industry_sorted_10.csv")
df_tk = pd.read_csv(csv_path, dtype=str)
cant_cal = ['S&J', 'WELL', 'S&J', 'WELL', 'ACAP', 'GSTEEL', 'MIPF', 'MNIT', 'QHBREIT', 'QHOP', 'TAPAC', 'TIF1', 'TU-PF', 'SGP', 'MANRIN']
cut_ind = ['Property & Construction','Agro & Food Industry','Technology']
all_ind = ['Industrial', 'Technology', 'Consumer Products', 'Property & Construction', 'Agro & Food Industry', 'Services', 'Resources', 'Financials']
fail = []

name_ind = {
    "Industrial" : "สินค้าอุตสาหกรรม",
    "Technology" : "เทคโนโลยี",
    "Consumer Products" : "สินค้าอุปโภคบริโภค",
    "Property & Construction": "อสังหาริมทรัพย์และก่อสร้าง",
    "Agro & Food Industry": "เกษตรและอุตสาหกรรมอาหาร",
    "Services" : "บริการ",
    "Resources" : "ทรัพยากร",
    "Financials" : "ธุรกิจการเงิน"
}

call_ind = {
    "Industrial" : "INDUS",
    "Technology" : "TECH",
    "Consumer Products" : "CONSUMP",
    "Property & Construction": "PROPCON",
    "Agro & Food Industry": "ARGO",
    "Services" : "SERVICE",
    "Resources" : "RESOURC",
    "Financials" : "FINCIAL"
}

year_window = 15

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
def forecast_stock_prices(years_forecast, n_sims=10000):
    if years_forecast <= 0:
        return {"Error": "Years forecast must be greater than 0."}
    
    yst = datetime.now().year - year_window
    start = f"{str(yst)}-01-01"
    end = datetime.today().strftime('%Y-%m-%d')

    res = {}
    res["Last_Time_for_index"] = None
    # res["Last_Time_for_SET"] = None
    # res["SET"] = None
    # ch = 1
    # try:
    #     df_daily = yf.download("^SET.BK", start=start, end=end, interval="1d", auto_adjust=False, progress=False)
    # except:
    #     ch = 0
    # if (ch and len(df_daily) >= 2):
    #     price_daily = df_daily["Close"].copy()
    #     price_daily = price_daily.dropna()
    #     price_daily.index = pd.to_datetime(price_daily.index)
    #     price_monthly = price_daily.resample('ME').last().dropna()
    #     log_returns_monthly = np.log(price_monthly / price_monthly.shift(1)).dropna()
    #     mu_y = float(log_returns_monthly.mean()) * 12.0
    #     sigma_y = float(log_returns_monthly.std(ddof=1)) * np.sqrt(12.0)
    #     S0 = price_monthly.iloc[-1]
    #     paths = monte_carlo_gbm_monthly(S0, mu_y, sigma_y, years_forecast, n_sims=n_sims)
    #     S0 = float(S0)
    #     last_price = paths[-1, :]

    #     median = np.median(last_price)
    #     mean = np.mean(last_price)
    #     prob_gain = np.mean(last_price >= S0)

    #     if not(np.isnan(median) or np.isnan(mean) or prob_gain == 0):
    #         res["SET"] = {
    #             "Name": "ตลาดหลักทรัพย์แห่งประเทศไทย",
    #             "start_price": float(S0),
    #             "median": float(median),
    #             "mean": float(mean),
    #             "prob_gain": float(prob_gain),
    #             "prob_loss": 1.0-float(prob_gain)
    #         }
    #         res["Last_Time_for_SET"] = str(end)
    
    for ind in all_ind:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        fn = str(ind) + ".csv"
        csv_path = os.path.join(BASE_DIR, "..", "data", "stockdata", fn)
        df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
        log_returns_monthly = np.log(df / df.shift(1)).dropna()
        mu_y = float(log_returns_monthly.mean()) * 12.0
        sigma_y = float(log_returns_monthly.std(ddof=1)) * np.sqrt(12.0)
        S0 = df.iloc[-1]
        paths = monte_carlo_gbm_monthly(S0, mu_y, sigma_y, years_forecast, n_sims=n_sims)
        S0 = float(S0)
        last_price = paths[-1, :]

        median = np.median(last_price)
        mean = np.mean(last_price)
        prob_gain = np.mean(last_price >= S0)

        if np.isnan(median) or np.isnan(mean) or prob_gain == 0:
            fail.append(ind)
            continue
        
        res[call_ind[ind]] = {
            "Name": name_ind[ind],
            "start_price": float(S0),
            "median": float(median),
            "mean": float(mean),
            "prob_gain": float(prob_gain),
            "prob_loss": 1.0-float(prob_gain)
        }

        if (res['Last_Time_for_index'] == None):
            res['Last_Time_for_index'] = str(df.index[-1])[:10]

    return res
#----------------------------------------------------------------------------------#

# For testing
# pprint(forecast_stock_prices(5))
# print("fail:", fail)