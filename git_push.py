import subprocess
from datetime import datetime
import shutil
import os

log_path = os.path.join(os.getcwd(), "git_push_log.txt")

def log(msg):
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

def ejecutar_comando(comando):
    resultado = subprocess.run(comando, capture_output=True, text=True, shell=True)
    log(f"=== Ejecutando: {comando} ===")
    if resultado.stdout:
        log(f"STDOUT:\n{resultado.stdout}")
    if resultado.stderr:
        log(f"STDERR:\n{resultado.stderr}")
    return resultado

# Verificamos que git exista
git_path = shutil.which("git")
if not git_path:
    log("❌ Git NO está disponible en este entorno.")
else:
    log(f"✅ Git está disponible en: {git_path}")

    ejecutar_comando("git add .")

    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M")
    mensaje_commit = f"Actualización automática - {fecha_hora}"
    ejecutar_comando(f'git commit -m "{mensaje_commit}"')

    ejecutar_comando("git push origin main")

log("📤 Finalizó script de git_push.py\n")
