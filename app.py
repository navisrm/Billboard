import asyncio
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, time as dt_time
from zoneinfo import ZoneInfo

from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from news_fetcher import get_news
from stock_fetcher import get_prices, get_tickers
from weather_fetcher import get_weather

MARKET_TZ = ZoneInfo("America/New_York")
MARKET_OPEN = dt_time(9, 30)
MARKET_CLOSE = dt_time(16, 0)
WEATHER_INTERVAL_SECONDS = 600
# news_fetcher only calls GNews when its cache is older than its own interval, so checking often is free.
NEWS_CHECK_SECONDS = 60


def is_market_open() -> bool:
    now = datetime.now(MARKET_TZ)
    if now.weekday() >= 5:
        return False
    return MARKET_OPEN <= now.time() < MARKET_CLOSE

load_dotenv()

FETCH_INTERVAL_SECONDS = 10
# Stocks are parked for now; set SHOW_STOCKS=true in .env to bring the stock board back.
SHOW_STOCKS = os.getenv("SHOW_STOCKS", "false").lower() == "true"
DISPLAY_NAME = os.getenv("DISPLAY_NAME", "Naveen")

state = {"prices": {}, "updated_at": None, "weather": None, "news": None}
state_lock = asyncio.Lock()

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


async def refresh_loop():
    tickers = get_tickers()
    while True:
        try:
            prices = await asyncio.to_thread(get_prices, tickers)
            async with state_lock:
                state["prices"] = prices
                state["updated_at"] = time.time()
        except Exception as exc:
            print(f"Failed to refresh prices: {exc}")
        await asyncio.sleep(FETCH_INTERVAL_SECONDS)


async def weather_loop():
    while True:
        try:
            weather = await asyncio.to_thread(get_weather)
            async with state_lock:
                state["weather"] = weather
        except Exception as exc:
            print(f"Failed to refresh weather: {exc}")
        await asyncio.sleep(WEATHER_INTERVAL_SECONDS)


async def news_loop():
    while True:
        try:
            news = await asyncio.to_thread(get_news)
            async with state_lock:
                state["news"] = news
        except Exception as exc:
            print(f"Failed to refresh news: {exc}")
        await asyncio.sleep(NEWS_CHECK_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    tasks = [asyncio.create_task(weather_loop()), asyncio.create_task(news_loop())]
    if SHOW_STOCKS:
        tasks.append(asyncio.create_task(refresh_loop()))
    yield
    for task in tasks:
        task.cancel()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def index(request: Request):
    if SHOW_STOCKS:
        return templates.TemplateResponse(request, "index.html", {"tickers": get_tickers()})
    return templates.TemplateResponse(request, "greeting.html", {"name": DISPLAY_NAME})


@app.get("/api/weather")
async def api_weather():
    async with state_lock:
        return JSONResponse({"weather": state["weather"]})


@app.get("/api/news")
async def api_news():
    async with state_lock:
        return JSONResponse(state["news"] or {"articles": [], "fetched_at": None, "error": None})


@app.get("/api/prices")
async def api_prices():
    async with state_lock:
        return JSONResponse({
            "prices": state["prices"],
            "updated_at": state["updated_at"],
            "market_open": is_market_open(),
            "weather": state["weather"],
        })


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
