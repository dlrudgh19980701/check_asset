from flask import (
    Flask,
    render_template,
    request,
    redirect
)

from db import (
    add_stock,
    get_stocks,
    delete_stock,
    add_manual_asset,
    get_manual_assets,
    delete_manual_asset
)

from crypto_price import (
    get_btc_price,
    get_eth_price
)

from stock_price import (
    get_current_price,
    get_usdkrw,
    get_stock_name
)

app = Flask(__name__)


@app.route("/")
def home():

    stocks = get_stocks()

    usdkrw = get_usdkrw()

    btc_price = get_btc_price() or 0

    eth_price = get_eth_price() or 0

    manual_assets = get_manual_assets()

    stock_assets = []

    stock_total = 0

    total_investment = 0

    category_totals = {}

    # -------------------------
    # 주식 처리
    # -------------------------
    for stock in stocks:

        stock_id = stock[0]
        market = stock[1]
        ticker = stock[2]
        quantity = stock[3]
        buy_price = stock[4]
        category = stock[5]

        current_price = get_current_price(
            market,
            ticker
        )

        stock_name = get_stock_name(
            market,
            ticker
        )

        if current_price is None:
            continue

        if market == "US":

            evaluation_krw = (
                quantity
                * current_price
                * usdkrw
            )

            investment = (
                quantity
                * buy_price
                * usdkrw
            )

        else:

            evaluation_krw = (
                quantity
                * current_price
            )

            investment = (
                quantity
                * buy_price
            )

        stock_total += evaluation_krw

        total_investment += investment

        profit = (
            (
                current_price
                - buy_price
            )
            / buy_price
        ) * 100

        stock_assets.append({

            "id": stock_id,

            "market": market,

            "ticker": ticker,

            "quantity": quantity,

            "buy_price": buy_price,

            "current_price": current_price,

            "profit": profit,

            "evaluation": evaluation_krw,

            "name": stock_name,

            "category": category

        })

        if category not in category_totals:

            category_totals[
                category
            ] = 0

        category_totals[
            category
        ] += evaluation_krw

    # -------------------------
    # 수동 자산 처리
    # -------------------------
    manual_total = 0

    manual_list = []

    for asset in manual_assets:

        asset_id = asset[0]

        name = asset[1]

        amount = asset[2]

        currency = asset[3]

        if currency == "KRW":

            amount_krw = amount
            category = "현금"

        elif currency == "USD":

            amount_krw = amount * usdkrw
            category = "달러"

        elif currency == "BTC":

            amount_krw = amount * btc_price
            category = "비트코인"

        elif currency == "ETH":

            amount_krw = amount * eth_price
            category = "이더리움"

        else:

            amount_krw = amount
            category = "기타"

        manual_total += amount_krw

        manual_list.append({

            "id": asset_id,

            "name": name,

            "amount": amount,

            "currency": currency,

            "evaluation": amount_krw

        })

        if category not in category_totals:

            category_totals[category] = 0

        category_totals[category] += amount_krw

    # -------------------------
    # 차트 데이터
    # -------------------------
    chart_labels = []

    chart_values = []

    for category, value in category_totals.items():

        chart_labels.append(
            category
        )

        chart_values.append(
            round(
                value,
                0
            )
        )

    # -------------------------
    # 전체 계산
    # -------------------------
    portfolio_investment = total_investment

    portfolio_evaluation = (

        stock_total

        + manual_total

    )

    total_profit = (

        portfolio_evaluation

        - portfolio_investment

    )

    if portfolio_investment > 0:

        total_profit_rate = (

            total_profit

            / portfolio_investment

        ) * 100

    else:

        total_profit_rate = 0

    total_asset = portfolio_evaluation

    # -------------------------
    # render
    # -------------------------
    return render_template(

        "index.html",


        stocks=stock_assets,

        manual_assets=manual_list,

        manual_total=manual_total,

        total_asset=total_asset,

        usdkrw=usdkrw,

        total_investment=portfolio_investment,

        total_profit=total_profit,

        total_profit_rate=total_profit_rate,

        portfolio_evaluation=portfolio_evaluation,

        chart_labels=chart_labels,

        chart_values=chart_values

    )


# -------------------------
# 주식 추가
# -------------------------
@app.route(
    "/add_stock",
    methods=["POST"]
)
def add_stock_route():

    market = request.form[
        "market"
    ]

    ticker = request.form[
        "ticker"
    ]

    quantity = float(
        request.form[
            "quantity"
        ]
    )

    buy_price = float(
        request.form[
            "buy_price"
        ]
    )

    category = request.form[
        "category"
    ]

    add_stock(

        market,

        ticker,

        quantity,

        buy_price,

        category

    )

    return redirect("/")


# -------------------------
# 주식 삭제
# -------------------------
@app.route(
    "/delete_stock/<int:stock_id>"
)
def delete_stock_route(stock_id):

    delete_stock(
        stock_id
    )

    return redirect("/")


# -------------------------
# 수동 자산 추가
# -------------------------
@app.route(
    "/add_manual_asset",
    methods=["POST"]
)
def add_manual_asset_route():

    name = request.form[
        "name"
    ]

    amount = float(
        request.form[
            "amount"
        ]
    )
    currency = request.form[
        "currency"
    ]

    add_manual_asset(
        name,
        amount,
        currency
    )

    return redirect("/")


# -------------------------
# 수동 자산 삭제
# -------------------------
@app.route(
    "/delete_manual_asset/<int:asset_id>"
)
def delete_manual_asset_route(asset_id):

    delete_manual_asset(
        asset_id
    )

    return redirect("/")


if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True

    )