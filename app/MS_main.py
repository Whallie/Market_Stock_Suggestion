from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from app import MS_FC as ms
import numpy as np
import pandas as pd
import math as ma
import os

#BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#csv_path = os.path.join(BASE_DIR, "..", "data", "th_index.csv")
#df_market = pd.read_csv(csv_path, dtype=str)

app = FastAPI(title="Market Stock List API")

class user_data(BaseModel):
    years_forecast : int = 10
    n_sims : int = 50000


@app.post("/market_stock/listing")

def simulate(req : user_data):
    res = ms.forecast_stock_prices(years_forecast=req.years_forecast, n_sims=req.n_sims)

    return res