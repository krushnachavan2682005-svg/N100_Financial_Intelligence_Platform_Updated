import sqlite3
import pprint

conn = sqlite3.connect('nifty100.db')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
schema = {}
for table in tables:
    table_name = table[0]
    cols = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    schema[table_name] = [c[1] for c in cols]

pprint.pprint(schema)
conn.close()
