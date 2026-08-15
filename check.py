import sqlite3
import pandas as pd

conn = sqlite3.connect('nifty100.db')
print(pd.read_sql("SELECT name FROM sqlite_master WHERE type='view'", conn))
