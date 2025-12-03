# To use API
### Here's the document (FastAPI): https://market-stock-suggestion.onrender.com/docs

### API Endpoint: https://market-stock-suggestion.onrender.com/market_stock/listing

## Init Body for POST request:
```json
{
  "years_forecast": 20,
  "n_sims": 5000
}
```

## Output:
```json
{
  "<Name of Industry>": {
    "Name": "<Name of Industry>",
    "start_price": <float>,
    "median": <float>,
    "mean": <float>,
    "prob_gain": <float>,
    "prob_loss": <float>
  }
}
```

### Description:
>**`Name of Industry`**: Name of industry index (All industry is from SET).<br>
**`start_price`**: Start price from data / Close price of stock at the earliest time of the time window (15 years).<br>
**`median`**: The median (or expected price) of this industry at the forecasted time.<br>
**`mean`**: The mean of this industry at the forecasted time.<br>
**`prob_gain`**: Chance of the close price at the forecast time being higher than the start price.<br>
**`prob_loss`**: Chance of the close price at the forecast time being lower than the start price.
