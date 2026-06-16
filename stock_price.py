import yfinance as yf


def get_current_price(
    market,
    ticker
):

    try:

        if market == "KR":

            # 한국 주식
            ticker = ticker + ".KS"

        stock = yf.Ticker(
            ticker
        )

        data = stock.history(
            period="1d"
        )

        if len(data) == 0:
            return None

        return float(
            data["Close"].iloc[-1]
        )

    except Exception:

        return None


def get_usdkrw():

    try:

        ticker = yf.Ticker(
            "USDKRW=X"
        )

        data = ticker.history(
            period="1d"
        )

        if len(data) == 0:
            return 1400

        return float(
            data["Close"].iloc[-1]
        )

    except Exception:

        return 1400
    
def get_stock_name(
    market,
    ticker
):

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

            return kr_names.get(
                ticker,
                ticker
            )

        stock = yf.Ticker(
            ticker
        )

        info = stock.info

        return info.get(
            "shortName",
            ticker
        )

    except Exception:

        return ticker