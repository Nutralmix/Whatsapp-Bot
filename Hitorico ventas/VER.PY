import sqlite3
import pandas as pd

conn = sqlite3.connect("historial_precios.db")
df = pd.read_sql_query("SELECT * FROM precios", conn)
conn.close()

print("🧾 Columnas actuales:")
for col in df.columns:
    print("-", col)
