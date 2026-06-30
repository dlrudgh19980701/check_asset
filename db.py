import sqlite3

DB_NAME = "portfolio.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


# =========================
# DB 초기화
# =========================
def init_db():

    conn = get_connection()
    cursor = conn.cursor()

    # -------------------------
    # 주식
    # -------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        market TEXT NOT NULL,
        ticker TEXT NOT NULL,
        quantity REAL NOT NULL,
        buy_price REAL NOT NULL,
        category TEXT NOT NULL
    )
    """)

    # -------------------------
    # 수동 자산
    # -------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS manual_assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


# =========================
# 주식
# =========================
def add_stock(
    market,
    ticker,
    quantity,
    buy_price,
    category
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO stocks
    (
        market,
        ticker,
        quantity,
        buy_price,
        category
    )
    VALUES (?, ?, ?, ?, ?)
    """, (
        market,
        ticker,
        quantity,
        buy_price,
        category
    ))

    conn.commit()
    conn.close()


def get_stocks():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        id,
        market,
        ticker,
        quantity,
        buy_price,
        category
    FROM stocks
    ORDER BY id DESC
    """)

    data = cursor.fetchall()

    conn.close()

    return data


def delete_stock(stock_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    DELETE FROM stocks
    WHERE id=?
    """, (stock_id,))

    conn.commit()
    conn.close()


# =========================
# 수동 자산
# =========================
def add_manual_asset(
    name,
    amount,
    currency
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO manual_assets
    (
        name,
        amount,
        currency
    )
    VALUES (?, ?, ?)
    """, (
        name,
        amount,
        currency
    ))

    conn.commit()
    conn.close()


def get_manual_assets():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        id,
        name,
        amount,
        currency
    FROM manual_assets
    ORDER BY id DESC
    """)

    data = cursor.fetchall()

    conn.close()

    return data


def delete_manual_asset(asset_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    DELETE FROM manual_assets
    WHERE id=?
    """, (asset_id,))

    conn.commit()
    conn.close()