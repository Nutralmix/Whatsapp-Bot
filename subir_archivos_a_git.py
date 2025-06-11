import subprocess
import os
from datetime import datetime

def ejecutar_comando(comando):
    resultado = subprocess.run(comando, capture_output=True, text=True, shell=True)
    if resultado.stdout:
        print("✅ STDOUT:", resultado.stdout.strip())
    if resultado.stderr:
        print("⚠️ STDERR:", resultado.stderr.strip())

def subir_cambios_a_git():
    carpeta = "static/archivos"
    if not os.path.exists(carpeta):
        print(f"❌ Carpeta no encontrada: {carpeta}")
        return

    print(f"📁 Verificando cambios en: {carpeta}")

    # Agregar archivos nuevos o modificados
    ejecutar_comando("git add static/archivos")

    # Verificar si hay algo para commitear
    resultado_status = subprocess.run("git status --porcelain", capture_output=True, text=True, shell=True)
    if not resultado_status.stdout.strip():
        print("🟡 No hay cambios nuevos para subir.")
        return

    # Commit
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M")
    mensaje_commit = f"Subida automática de archivos desde el panel - {fecha_hora}"
    ejecutar_comando(f'git commit -m "{mensaje_commit}"')

    # Push
    ejecutar_comando("git push origin main")

    print("🚀 Archivos subidos correctamente a GitHub.")

if __name__ == "__main__":
    subir_cambios_a_git()
