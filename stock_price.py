import logging
import functools
import time
import yfinance as yf
import io
import sys
import requests
import pandas as pd
import threading
from contextlib import redirect_stdout, redirect_stderr

# Reduce noisy logs from yfinance/urllib3 when a symbol is not found
logging.getLogger("yfinance").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.WARNING)

_US_RSI_CACHE = None
_US_RSI_CACHE_AT = 0
_US_RSI_CACHE_TTL = 900
_US_RSI_REFRESHING = False
_US_RSI_ERROR = None
_US_RSI_RETRY_AT = 0
_US_RSI_LOCK = threading.Lock()


def ttl_cache(ttl_seconds):
    def decorator(func):
        cache = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            now = time.monotonic()
            cached = cache.get(key)
            if cached and now - cached[1] < ttl_seconds:
                return cached[0]

            value = func(*args, **kwargs)
            cache[key] = (value, now)
            return value

        return wrapper

    return decorator


@ttl_cache(300)
def get_current_price(market, ticker):
    try:
        if market == "KR":
            ticker = ticker + ".KS"

        stock = yf.Ticker(ticker)
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        with redirect_stdout(buf_out), redirect_stderr(buf_err):
            data = stock.history(period="1d", timeout=8)

        if data is None or len(data) == 0:
            return None

        return float(data["Close"].iloc[-1])

    except Exception:
        # swallow errors and return None so the app can skip delisted symbols
        return None


@ttl_cache(300)
def get_usdkrw():
    try:
        ticker = yf.Ticker("USDKRW=X")
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        with redirect_stdout(buf_out), redirect_stderr(buf_err):
            data = ticker.history(period="1d", timeout=8)

        if data is None or len(data) == 0:
            return 1400

        return float(data["Close"].iloc[-1])

    except Exception:
        return 1400


@ttl_cache(3600)
def get_stock_name(market, ticker):
    try:
        if market == "KR":
            kr_names = {
                "005930": "삼성전자",
                "000660": "SK하이닉스",
                "035420": "NAVER",
                "005380": "현대차",
                "012330": "현대모비스",
                "051910": "LG화학",
                "035720": "카카오",
                "488770": "Kodex 머니마켓 엑티브",
                "449190": "Kodex 미국나스닥100(H)",
                "472160": "TIGER 미국테크 TOP10 INDXX(H)",
                "449180": "Kodex 미국S&P500(H)",
                "132030": "Kodex 골드선물(H)",
                "411060": "ACE KRX금현물",
                "497570": "TIGER 필라델피아AI반도체나스닥",
                "0151S0": "KODEX 미국AI반도체TOP3 플러스"
            }

            return kr_names.get(ticker, ticker)

        response = requests.get(
            "https://query1.finance.yahoo.com/v1/finance/search",
            params={"q": ticker, "quotesCount": 5, "newsCount": 0},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5,
        )
        response.raise_for_status()
        matches = response.json().get("quotes", [])
        exact_match = next(
            (quote for quote in matches if quote.get("symbol") == ticker),
            None,
        )
        if exact_match:
            return (
                exact_match.get("longname")
                or exact_match.get("shortname")
                or ticker
            )

        return ticker

    except Exception:
        return ticker


def get_us_large_cap_rsi():
    global _US_RSI_REFRESHING, _US_RSI_ERROR

    now = time.monotonic()
    with _US_RSI_LOCK:
        cache_is_fresh = (
            _US_RSI_CACHE is not None
            and now - _US_RSI_CACHE_AT < _US_RSI_CACHE_TTL
        )

        if not cache_is_fresh and not _US_RSI_REFRESHING and now >= _US_RSI_RETRY_AT:
            _US_RSI_REFRESHING = True
            _US_RSI_ERROR = None
            threading.Thread(target=_refresh_us_large_cap_rsi, daemon=True).start()

        return {
            "groups": _US_RSI_CACHE or {"low": [], "high": []},
            "loading": _US_RSI_REFRESHING,
            "error": _US_RSI_ERROR,
        }


def _refresh_us_large_cap_rsi():
    global _US_RSI_CACHE, _US_RSI_CACHE_AT
    global _US_RSI_REFRESHING, _US_RSI_ERROR, _US_RSI_RETRY_AT

    try:
        response = requests.get(
            "https://query2.finance.yahoo.com/v1/finance/screener/predefined/saved",
            params={
                "formatted": "false",
                "lang": "en-US",
                "region": "US",
                "scrIds": "largest_market_cap",
                "count": 250,
            },
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()["finance"]["result"][0]
        quotes = result.get("quotes", [])
        us_exchanges = {"NYQ", "NMS", "NGM", "NCM", "ASE"}
        quotes = [
            quote
            for quote in quotes
            if quote.get("symbol")
            and quote.get("quoteType") == "EQUITY"
            and quote.get("exchange") in us_exchanges
            and isinstance(quote.get("marketCap"), (int, float))
            and quote["marketCap"] > 0
        ]
        quotes.sort(key=lambda quote: quote["marketCap"], reverse=True)
        quotes = quotes[:100]
        tickers = [quote["symbol"] for quote in quotes]

        if len(tickers) < 100:
            raise ValueError("Yahoo Finance returned fewer than 100 eligible US stocks")

        history = yf.download(
            tickers=tickers,
            period="3mo",
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=4,
            timeout=10,
        )
        close_prices = history["Close"]
        if isinstance(close_prices, pd.Series):
            close_prices = close_prices.to_frame()

        name_by_ticker = {
            quote["symbol"]: (
                quote.get("longName")
                or quote.get("shortName")
                or quote.get("displayName")
                or quote["symbol"]
            )
            for quote in quotes
            if quote.get("symbol")
        }
        market_cap_by_ticker = {
            quote["symbol"]: quote["marketCap"]
            for quote in quotes
            if quote.get("symbol")
        }

        available_tickers = [
            ticker for ticker in tickers if ticker in close_prices.columns
        ]
        close_prices = close_prices[available_tickers]
        changes = close_prices.diff()
        average_gains = changes.clip(lower=0).ewm(
            alpha=1 / 14,
            min_periods=14,
            adjust=False,
        ).mean()
        average_losses = (-changes.clip(upper=0)).ewm(
            alpha=1 / 14,
            min_periods=14,
            adjust=False,
        ).mean()
        relative_strength = average_gains / average_losses.replace(0, float("nan"))
        rsi_values = 100 - (100 / (1 + relative_strength))
        rsi_values = rsi_values.mask(average_losses == 0, 100)

        low_rsi = []
        high_rsi = []

        for rank, ticker in enumerate(tickers, start=1):
            if ticker not in rsi_values.columns:
                continue

            close = close_prices[ticker].dropna()
            rsi = rsi_values[ticker].dropna()

            if rsi.empty:
                continue

            latest_rsi = float(rsi.iloc[-1])
            item = {
                "rank": rank,
                "ticker": ticker,
                "name": name_by_ticker.get(ticker, ticker),
                "market_cap": market_cap_by_ticker[ticker],
                "price": float(close.iloc[-1]),
                "rsi": latest_rsi,
            }

            if latest_rsi <= 40:
                low_rsi.append(item)
            elif latest_rsi >= 60:
                high_rsi.append(item)

        with _US_RSI_LOCK:
            _US_RSI_CACHE = {"low": low_rsi, "high": high_rsi}
            _US_RSI_CACHE_AT = time.monotonic()
            _US_RSI_ERROR = None
            _US_RSI_RETRY_AT = 0

    except Exception as error:
        logging.exception("Unable to load US large-cap RSI data")
        with _US_RSI_LOCK:
            _US_RSI_ERROR = "미국 대형주 RSI 데이터를 불러오지 못했습니다."
            _US_RSI_RETRY_AT = time.monotonic() + 60
    finally:
        with _US_RSI_LOCK:
            _US_RSI_REFRESHING = False