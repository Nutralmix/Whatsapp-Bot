import sqlite3

conn = sqlite3.connect("historial_precios.db")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS precios")
conn.commit()
conn.close()

print("🧹 Tabla 'precios' eliminada.")
