import sqlite3

conn = sqlite3.connect("portfolio.db")

cursor = conn.cursor()

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

conn.commit()
conn.close()

print("DB 생성 완료")