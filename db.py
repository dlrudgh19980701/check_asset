import os
import sqlite3
import psycopg

DATABASE_URL = os.environ["DATABASE_URL"]


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