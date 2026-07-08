from db import init_db

print("Creating tables...")
init_db()
print("Tables created.")

import os
import sqlite3
import psycopg

# 기존 SQLite
sqlite_conn = sqlite3.connect("portfolio.db")
sqlite_cur = sqlite_conn.cursor()

# PostgreSQL (Supabase)
pg_conn = psycopg.connect(os.environ["DATABASE_URL"])
pg_cur = pg_conn.cursor()

# =========================
# stocks
# =========================
sqlite_cur.execute("""
SELECT
    market,
    ticker,
    quantity,
    buy_price,
    category
FROM stocks
""")

stocks = sqlite_cur.fetchall()

for stock in stocks:

    pg_cur.execute("""
    INSERT INTO stocks
    (
        market,
        ticker,
        quantity,
        buy_price,
        category
    )
    VALUES (%s,%s,%s,%s,%s)
    """, stock)

# =========================
# manual_assets
# =========================
sqlite_cur.execute("""
SELECT
    name,
    amount,
    currency
FROM manual_assets
""")

assets = sqlite_cur.fetchall()

for asset in assets:

    pg_cur.execute("""
    INSERT INTO manual_assets
    (
        name,
        amount,
        currency
    )
    VALUES (%s,%s,%s)
    """, asset)

pg_conn.commit()

sqlite_conn.close()
pg_conn.close()

print("Migration Complete!")