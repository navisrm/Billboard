import math
import time

import yfinance as yf

INDEXES = [
    ("^GSPC", "S&P 500"),
    ("^IXIC", "Nasdaq"),
    ("^DJI", "Dow"),
    ("^GSPTSE", "TSX"),
]

# Sector performance is the SPDR sector ETF; the stocks are large holdings in that sector.
SECTORS = [
    {"key": "tech", "name": "Technology", "etf": "XLK", "stocks": ["AAPL", "MSFT", "NVDA", "AVGO", "ORCL"]},
    {"key": "comm", "name": "Communication", "etf": "XLC", "stocks": ["GOOGL", "META", "NFLX", "DIS", "TMUS"]},
    {"key": "disc", "name": "Consumer Discretionary", "etf": "XLY", "stocks": ["AMZN", "TSLA", "HD", "MCD", "NKE"]},
    {"key": "fin", "name": "Financials", "etf": "XLF", "stocks": ["JPM", "V", "MA", "BAC", "WFC"]},
    {"key": "health", "name": "Health Care", "etf": "XLV", "stocks": ["LLY", "UNH", "JNJ", "ABBV", "MRK"]},
    {"key": "ind", "name": "Industrials", "etf": "XLI", "stocks": ["GE", "CAT", "RTX", "HON", "UNP"]},
    {"key": "staples", "name": "Consumer Staples", "etf": "XLP", "stocks": ["WMT", "PG", "COST", "KO", "PEP"]},
    {"key": "energy", "name": "Energy", "etf": "XLE", "stocks": ["XOM", "CVX", "COP", "SLB", "EOG"]},
    {"key": "util", "name": "Utilities", "etf": "XLU", "stocks": ["NEE", "SO", "DUK", "CEG", "AEP"]},
    {"key": "re", "name": "Real Estate", "etf": "XLRE", "stocks": ["PLD", "AMT", "EQIX", "WELL", "SPG"]},
    {"key": "mat", "name": "Materials", "etf": "XLB", "stocks": ["LIN", "SHW", "APD", "FCX", "NEM"]},
]

# Short display names, so the screen doesn't need a per-ticker info lookup.
NAMES = {
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "Nvidia", "AVGO": "Broadcom", "ORCL": "Oracle",
    "GOOGL": "Alphabet", "META": "Meta", "NFLX": "Netflix", "DIS": "Disney", "TMUS": "T-Mobile",
    "AMZN": "Amazon", "TSLA": "Tesla", "HD": "Home Depot", "MCD": "McDonald's", "NKE": "Nike",
    "JPM": "JPMorgan", "V": "Visa", "MA": "Mastercard", "BAC": "Bank of America", "WFC": "Wells Fargo",
    "LLY": "Eli Lilly", "UNH": "UnitedHealth", "JNJ": "Johnson & Johnson", "ABBV": "AbbVie", "MRK": "Merck",
    "GE": "GE Aerospace", "CAT": "Caterpillar", "RTX": "RTX", "HON": "Honeywell", "UNP": "Union Pacific",
    "WMT": "Walmart", "PG": "Procter & Gamble", "COST": "Costco", "KO": "Coca-Cola", "PEP": "PepsiCo",
    "XOM": "Exxon Mobil", "CVX": "Chevron", "COP": "ConocoPhillips", "SLB": "SLB", "EOG": "EOG Resources",
    "NEE": "NextEra Energy", "SO": "Southern Co", "DUK": "Duke Energy", "CEG": "Constellation", "AEP": "AEP",
    "PLD": "Prologis", "AMT": "American Tower", "EQIX": "Equinix", "WELL": "Welltower", "SPG": "Simon Property",
    "LIN": "Linde", "SHW": "Sherwin-Williams", "APD": "Air Products", "FCX": "Freeport-McMoRan", "NEM": "Newmont",
}


def _quotes(symbols):
    # One batched request for every symbol; each value is the latest close vs the previous session.
    closes = yf.download(symbols, period="5d", interval="1d", progress=False, auto_adjust=False, threads=True)["Close"]
    quotes = {}
    for symbol in symbols:
        series = closes[symbol].dropna() if symbol in closes else None
        if series is None or len(series) < 2:
            continue
        price, previous = float(series.iloc[-1]), float(series.iloc[-2])
        if math.isnan(price) or not previous:
            continue
        quotes[symbol] = {"price": price, "change_pct": (price / previous - 1) * 100}
    return quotes


def get_market():
    symbols = [s for s, _ in INDEXES] + [s["etf"] for s in SECTORS] + [t for s in SECTORS for t in s["stocks"]]
    quotes = _quotes(symbols)

    def quote(symbol, name):
        q = quotes.get(symbol)
        return {"symbol": symbol, "name": name, "price": q["price"] if q else None,
                "change_pct": q["change_pct"] if q else None}

    return {
        "indexes": [quote(symbol, name) for symbol, name in INDEXES],
        "sectors": [
            {
                "key": sector["key"],
                **quote(sector["etf"], sector["name"]),
                "stocks": [quote(t, NAMES.get(t, t)) for t in sector["stocks"]],
            }
            for sector in SECTORS
        ],
        "updated_at": time.time(),
    }
