import os

import yfinance as yf
from dotenv import load_dotenv

load_dotenv()


def get_tickers():
    raw = os.getenv("TICKERS", "DELL")
    return [t.strip().upper() for t in raw.split(",") if t.strip()]


def get_prices(tickers):
    prices = {}
    for ticker in tickers:
        info = yf.Ticker(ticker).fast_info
        price = info["last_price"]
        previous_close = info["previous_close"]
        change = price - previous_close
        change_percent = (change / previous_close) * 100 if previous_close else 0
        prices[ticker] = {
            "price": price,
            "change": change,
            "change_percent": change_percent,
        }
    return prices
