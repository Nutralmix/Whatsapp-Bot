import os
import unicodedata
import shutil

BASE_DIR = os.path.join("static", "archivos")

def normalizar(texto):
    texto = unicodedata.normalize('NFD', texto)
    return ''.join(c for c in texto if unicodedata.category(c) != 'Mn')

def renombrar_carpetas():
    for carpeta in os.listdir(BASE_DIR):
        ruta_original = os.path.join(BASE_DIR, carpeta)

        if os.path.isdir(ruta_original):
            carpeta_normalizada = normalizar(carpeta)

            if carpeta != carpeta_normalizada:
                ruta_nueva = os.path.join(BASE_DIR, carpeta_normalizada)

                if os.path.exists(ruta_nueva):
                    print(f"⚠️ Ya existe: {ruta_nueva}, saltando...")
                    continue

                print(f"🔄 Renombrando: {carpeta} → {carpeta_normalizada}")
                shutil.move(ruta_original, ruta_nueva)

if __name__ == "__main__":
    renombrar_carpetas()
    print("✅ Renombrado finalizado.")
