import sqlite3
import pandas as pd

# 1. Conectarse a la base de datos
conn = sqlite3.connect("historial_precios.db")

# 2. Leer toda la tabla "precios"
try:
    df = pd.read_sql_query("SELECT * FROM precios", conn)
    print(df)
except Exception as e:
    print("❌ Error al leer la base de datos:", e)
finally:
    conn.close()
