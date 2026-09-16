import logging
import yfinance as yf
import io
import sys
from contextlib import redirect_stdout, redirect_stderr
import time
import functools


# Simple in-memory TTL cache decorator to avoid repeated external calls
def ttl_cache(ttl_seconds: int):
    def decorator(func):
        cache = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            now = time.time()
            if key in cache:
                value, ts = cache[key]
                if now - ts < ttl_seconds:
                    return value
            value = func(*args, **kwargs)
            cache[key] = (value, now)
            return value

        return wrapper

    return decorator

# Reduce noisy logs from yfinance/urllib3 when a symbol is not found
logging.getLogger("yfinance").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.WARNING)


@ttl_cache(300)  # cache price for 5 minutes
def get_current_price(market, ticker):
    try:
        if market == "KR":
            ticker = ticker + ".KS"

        stock = yf.Ticker(ticker)
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        with redirect_stdout(buf_out), redirect_stderr(buf_err):
            data = stock.history(period="1d")

        if data is None or len(data) == 0:
            return None

        return float(data["Close"].iloc[-1])

    except Exception:
        # swallow errors and return None so the app can skip delisted symbols
        return None


def get_usdkrw():
    try:
        ticker = yf.Ticker("USDKRW=X")
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        with redirect_stdout(buf_out), redirect_stderr(buf_err):
            data = ticker.history(period="1d")

        if data is None or len(data) == 0:
            return 1400

        return float(data["Close"].iloc[-1])

    except Exception:
        return 1400


@ttl_cache(3600)  # cache stock name for 1 hour
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

        stock = yf.Ticker(ticker)
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        with redirect_stdout(buf_out), redirect_stderr(buf_err):
            info = stock.info

        return info.get("shortName", ticker)

    except Exception:
        return ticker