import sqlite3
import pandas as pd
conn = sqlite3.connect("historial_precios.db")
df = pd.read_sql_query("SELECT `Nombre del producto`, `Variacion 9dj`, `Variacion TL` FROM precios", conn)
print(df.head(10))
conn.close()
