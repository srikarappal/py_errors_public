import thinking_sdk_client as thinking
thinking.start(config_file="thinkingsdk.yaml")

import psycopg2

def main():
    conn = psycopg2.connect("dbname=app user=app password=secret host=localhost")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE
        )
    """)
    conn.commit()
    
    try:
        cur.execute("INSERT INTO users (email) VALUES (%s)", ("ada@example.com",))
        cur.execute("INSERT INTO users (email) VALUES (%s)", ("ada@example.com",))  # UNIQUE violation
        conn.commit()
    except Exception as e:
        print("Insert failed:", e)
    
    # ❌ Transaction is still aborted; next execute explodes:
    cur.execute("SELECT COUNT(*) FROM users")  # raises InFailedSqlTransaction
    print(cur.fetchone())

main()
