
import thinking_sdk_client as thinking
thinking.start(config_file="thinkingsdk.yaml")

import sqlite3

conn = sqlite3.connect(":memory:")
cur = conn.cursor()
cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")

# Wrong placeholders for sqlite3
cur.execute("INSERT INTO users (name) VALUES (%s)", ("Ada",))   # raises OperationalError
conn.commit()
