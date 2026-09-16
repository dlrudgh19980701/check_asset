import os
import sqlite3
import psycopg

# Load .env automatically in development (optional). If a `.env` file
# exists in the project root, `load_dotenv()` will populate environment
# variables before we read `DATABASE_URL`.
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # python-dotenv is optional in production; continue if it's missing.
    pass

# Prefer an explicit environment variable, but give a clear error if missing
# to avoid an unhelpful KeyError. For local development you can set
# DATABASE_URL to a Postgres URL (recommended) or to a sqlite URL
# like "sqlite:///data.db".
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "Environment variable DATABASE_URL is not set.\n"
        "Set it before running the app (example):\n"
        "  PowerShell: $env:DATABASE_URL='postgresql://user:pass@host:5432/dbname'\n"
        "  CMD: set DATABASE_URL=postgresql://user:pass@host:5432/dbname\n"
        "Or create a .env file and add DATABASE_URL there (see .env.example).\n"
        "For a quick local fallback you may set: DATABASE_URL=sqlite:///data.db"
    )


def get_connection():
    return psycopg.connect(DATABASE_URL)


# =========================
# DB 초기화
# =========================
def init_db():

    with get_connection() as conn:
        with conn.cursor() as cursor:

            # -------------------------
            # 주식
            # -------------------------
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                id SERIAL PRIMARY KEY,
                market TEXT NOT NULL,
                ticker TEXT NOT NULL,
                quantity DOUBLE PRECISION NOT NULL,
                buy_price DOUBLE PRECISION NOT NULL,
                category TEXT NOT NULL
            )
            """)

            # -------------------------
            # 수동 자산
            # -------------------------
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS manual_assets (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                amount DOUBLE PRECISION NOT NULL,
                currency TEXT NOT NULL
            )
            """)


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

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
            INSERT INTO stocks
            (
                market,
                ticker,
                quantity,
                buy_price,
                category
            )
            VALUES (%s, %s, %s, %s, %s)
            """, (
                market,
                ticker,
                quantity,
                buy_price,
                category
            ))


def get_stocks():

    with get_connection() as conn:
        with conn.cursor() as cursor:

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

            return cursor.fetchall()


def get_stock_by_market_and_ticker(market, ticker):

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
            SELECT
                id,
                market,
                ticker,
                quantity,
                buy_price,
                category
            FROM stocks
            WHERE market=%s AND ticker=%s
            """, (market, ticker))

            return cursor.fetchone()


def update_stock_quantity_and_price(stock_id, new_quantity, new_buy_price, category):

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
            UPDATE stocks
            SET quantity=%s, buy_price=%s, category=%s
            WHERE id=%s
            """, (new_quantity, new_buy_price, category, stock_id))


def delete_stock(stock_id):

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
            DELETE FROM stocks
            WHERE id=%s
            """, (stock_id,))


# =========================
# 수동 자산
# =========================
def add_manual_asset(
    name,
    amount,
    currency
):

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
            INSERT INTO manual_assets
            (
                name,
                amount,
                currency
            )
            VALUES (%s, %s, %s)
            """, (
                name,
                amount,
                currency
            ))


def get_manual_asset(asset_id):

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
            SELECT id, name, amount, currency
            FROM manual_assets
            WHERE id=%s
            """, (asset_id,))

            return cursor.fetchone()


def get_manual_asset_by_name_currency(name, currency):

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
            SELECT id, name, amount, currency
            FROM manual_assets
            WHERE name=%s AND currency=%s
            """, (name, currency))

            return cursor.fetchone()


def update_manual_asset_amount(asset_id, new_amount):

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
            UPDATE manual_assets
            SET amount=%s
            WHERE id=%s
            """, (new_amount, asset_id))


def get_manual_assets():

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
            SELECT
                id,
                name,
                amount,
                currency
            FROM manual_assets
            ORDER BY id DESC
            """)

            return cursor.fetchall()


def delete_manual_asset(asset_id):

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
            DELETE FROM manual_assets
            WHERE id=%s
            """, (asset_id,))