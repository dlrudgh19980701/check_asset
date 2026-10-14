import logging
import time
import yfinance as yf
import io
import sys
import requests
import pandas as pd
from contextlib import redirect_stdout, redirect_stderr

# Reduce noisy logs from yfinance/urllib3 when a symbol is not found
logging.getLogger("yfinance").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.WARNING)

_US_RSI_CACHE = None
_US_RSI_CACHE_AT = 0
_US_RSI_CACHE_TTL = 900


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


def get_us_large_cap_rsi():
    global _US_RSI_CACHE, _US_RSI_CACHE_AT

    if (
        _US_RSI_CACHE is not None
        and time.monotonic() - _US_RSI_CACHE_AT < _US_RSI_CACHE_TTL
    ):
        return _US_RSI_CACHE

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
            timeout=15,
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
            threads=True,
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

        low_rsi = []
        high_rsi = []

        for rank, ticker in enumerate(tickers, start=1):
            if ticker not in close_prices.columns:
                continue

            close = close_prices[ticker].dropna()
            change = close.diff()
            average_gain = change.clip(lower=0).ewm(
                alpha=1 / 14,
                min_periods=14,
                adjust=False,
            ).mean()
            average_loss = (-change.clip(upper=0)).ewm(
                alpha=1 / 14,
                min_periods=14,
                adjust=False,
            ).mean()
            relative_strength = average_gain / average_loss.replace(0, float("nan"))
            rsi = 100 - (100 / (1 + relative_strength))
            rsi = rsi.mask(average_loss == 0, 100).dropna()

            if rsi.empty:
                continue

            latest_rsi = float(rsi.iloc[-1])
            item = {
                "rank": rank,
                "ticker": ticker,
                "name": name_by_ticker.get(ticker, ticker),
                "market_cap": next(
                    quote["marketCap"]
                    for quote in quotes
                    if quote["symbol"] == ticker
                ),
                "price": float(close.iloc[-1]),
                "rsi": latest_rsi,
            }

            if latest_rsi <= 40:
                low_rsi.append(item)
            elif latest_rsi >= 60:
                high_rsi.append(item)

        _US_RSI_CACHE = {"low": low_rsi, "high": high_rsi}
        _US_RSI_CACHE_AT = time.monotonic()
        return _US_RSI_CACHE

    except Exception as error:
        logging.exception("Unable to load US large-cap RSI data")
        raise RuntimeError("미국 대형주 RSI 데이터를 불러오지 못했습니다.") from error