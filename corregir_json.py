import json

# Ruta del archivo original
ARCHIVO_JSON = "empleados.json"
ARCHIVO_SALIDA = "empleados_corregido.json"

# Cargar el archivo original
with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
    empleados = json.load(f)

# Procesar cada registro
for clave, datos in empleados.items():
    # Agregar legajo si falta
    if "legajo" not in datos:
        datos["legajo"] = str(clave)

    # Agregar rol si falta
    if "rol" not in datos:
        datos["rol"] = "empleado"

# Guardar el nuevo archivo
with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as f:
    json.dump(empleados, f, ensure_ascii=False, indent=4)

print(f"✅ Archivo corregido guardado como: {ARCHIVO_SALIDA}")
