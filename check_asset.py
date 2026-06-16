# check_asset.py

import os
import pyupbit

ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY")
SECRET_KEY = os.getenv("UPBIT_SECRET_KEY")

def get_asset_data():

    upbit = pyupbit.Upbit(
        ACCESS_KEY,
        SECRET_KEY
    )

    balances = upbit.get_balances()

    total = 0

    assets = []

    crypto_investment = 0

    coin_names = {

        "BTC": "비트코인",
        "ETH": "이더리움",
        "XRP": "리플",
        "SOL": "솔라나",
        "DOGE": "도지코인"

    }

    for asset in balances:

        currency = asset["currency"]

        balance = float(
            asset["balance"]
        )

        avg_buy_price = float(
            asset["avg_buy_price"]
        )

        # -------------------------
        # 업비트 원화
        # -------------------------
        if currency == "KRW":

            total += balance

            assets.append({

                "name": "업비트_현금",

                "category": "현금",

                "currency": "KRW",

                "balance": balance,

                "evaluation": balance,

                "investment": balance,

                "profit": 0

            })

            continue

        # -------------------------
        # 코인
        # -------------------------
        current_price = pyupbit.get_current_price(
            f"KRW-{currency}"
        )

        if current_price:

            evaluation = (
                balance
                * current_price
            )

            investment = (
                balance
                * avg_buy_price
            )

            profit = (
                evaluation
                - investment
            )

            crypto_investment += (
                investment
            )

            total += evaluation

            coin_name = coin_names.get(
                currency,
                currency
            )

            assets.append({

                "name": coin_name,

                # 차트에서 코인별로 분리
                "category": coin_name,

                "currency": currency,

                "balance": balance,

                "avg_buy_price": avg_buy_price,

                "evaluation": evaluation,

                "investment": investment,

                "profit": profit

            })

    return {

        "total": total,

        "investment": crypto_investment,

        "assets": assets

    }