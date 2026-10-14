from flask import (
    Flask,
    render_template,
    request,
    redirect
)

from db import (
    init_db,
    add_stock,
    get_stocks,
    delete_stock,
    add_manual_asset,
    get_manual_assets,
    delete_manual_asset
)
from db import get_manual_asset_by_name_currency
from db import (
    get_stock_by_market_and_ticker,
    update_stock_quantity_and_price,
    get_manual_asset,
    update_manual_asset_amount
)

from crypto_price import (
    get_btc_price,
    get_eth_price
)

from stock_price import (
    get_current_price,
    get_usdkrw,
    get_stock_name,
    get_us_large_cap_rsi,
)

app = Flask(__name__)
init_db()

@app.route("/")
def home():

    stocks = get_stocks()

    usdkrw = get_usdkrw()

    btc_price = get_btc_price() or 0

    eth_price = get_eth_price() or 0

    manual_assets = get_manual_assets()

    try:
        us_rsi_groups = get_us_large_cap_rsi()
        us_rsi_error = None
    except RuntimeError as error:
        us_rsi_groups = {"low": [], "high": []}
        us_rsi_error = str(error)

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
            category = "현금"

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

        chart_values=chart_values,

        us_rsi_groups=us_rsi_groups,

        us_rsi_error=us_rsi_error

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

    # If same name+currency exists, sum the amounts instead of creating duplicate
    existing = get_manual_asset_by_name_currency(name, currency)
    if existing:
        asset_id = existing[0]
        old_amount = existing[2]
        new_amount = old_amount + amount
        update_manual_asset_amount(asset_id, new_amount)
    else:
        add_manual_asset(
            name,
            amount,
            currency
        )

    return redirect("/")


# -------------------------
# 주식 매수/매도
# -------------------------
@app.route(
    "/trade",
    methods=["POST"]
)
def trade_route():

    action = request.form["action"]  # 'buy' or 'sell'

    market = request.form["market"]

    ticker = request.form["ticker"]

    quantity = float(request.form["quantity"])

    price = float(request.form["price"])  # unit price entered by user

    category = request.form.get("category", "")

    source_id = int(request.form.get("source_id", "0") or "0")

    source = None
    source_amount = None
    source_currency = None

    if source_id != 0:
        source = get_manual_asset(source_id)
        if not source:
            return redirect("/")
        source_amount = source[2]
        source_currency = source[3]

    usdkrw = get_usdkrw()

    # cost/proceed calculation is only needed when we update a manual asset
    cost = None
    if source is not None:
        # cost/proceed in source currency
        if market == "US":
            # price is in USD
            if source_currency == "USD":
                cost = quantity * price
            else:
                cost = quantity * price * usdkrw
        else:
            # KR market, price in KRW
            if source_currency == "KRW":
                cost = quantity * price
            else:
                # convert source currency to KRW for simplicity
                if source_currency == "USD":
                    cost = quantity * price / usdkrw
                else:
                    # other currencies not supported for trade
                    return redirect("/")

    # BUY
    if action == "buy":

        # if a source is provided, check and deduct funds
        if source is not None:
            if source_amount < cost:
                return redirect("/")

            # deduct funds
            new_source_amount = source_amount - cost
            update_manual_asset_amount(source_id, new_source_amount)

        # add or update stock
        existing = get_stock_by_market_and_ticker(market, ticker)
        if existing:
            stock_id = existing[0]
            old_qty = existing[3]
            old_price = existing[4]
            new_qty = old_qty + quantity
            # weighted average buy price
            new_buy_price = ((old_qty * old_price) + (quantity * price)) / new_qty
            update_stock_quantity_and_price(stock_id, new_qty, new_buy_price, category)
        else:
            add_stock(market, ticker, quantity, price, category or "주식")

    # SELL
    elif action == "sell":

        existing = get_stock_by_market_and_ticker(market, ticker)
        if not existing:
            return redirect("/")

        stock_id = existing[0]
        old_qty = existing[3]
        if old_qty < quantity:
            return redirect("/")

        # reduce stock
        remaining = old_qty - quantity
        if remaining <= 0:
            delete_stock(stock_id)
        else:
            # preserve existing category when selling
            update_stock_quantity_and_price(stock_id, remaining, existing[4], existing[5])

        # credit funds (only if a source account was selected)
        if source is not None:
            new_source_amount = source_amount + cost
            update_manual_asset_amount(source_id, new_source_amount)

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


import os

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )