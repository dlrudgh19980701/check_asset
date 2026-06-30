import requests


def get_crypto_price(market):

    url = (
        "https://api.upbit.com/v1/ticker"
        f"?markets={market}"
    )

    try:

        response = requests.get(
            url,
            timeout=5
        )

        response.raise_for_status()

        data = response.json()

        return data[0]["trade_price"]

    except Exception as e:

        print(
            f"{market} price error:",
            e
        )

        return None


def get_btc_price():

    return get_crypto_price(
        "KRW-BTC"
    )


def get_eth_price():

    return get_crypto_price(
        "KRW-ETH"
    )