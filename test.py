import psycopg

conn = psycopg.connect(
    host="db.rdrsxgbzgtiizbruelsr.supabase.co",
    dbname="postgres",
    user="postgres",
    password="2801msskk!!",
    port=5432
)

print("Connected!")
conn.close()