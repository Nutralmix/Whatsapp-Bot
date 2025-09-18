import subprocess
from datetime import datetime
import shutil
import os

log_path = os.path.join(os.getcwd(), "git_push_log.txt")

def log(msg):
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

def ejecutar_comando(comando):
    log(f"=== Ejecutando: {comando} ===")
    resultado = subprocess.run(comando, capture_output=True, text=True, shell=True)
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

    # Intentamos hacer pull antes del push
    resultado_pull = ejecutar_comando("git pull origin main --no-edit")
    if resultado_pull.returncode != 0:
        log("⚠️ Falló el 'git pull'. Intentando continuar de todas formas...")

    # Intentamos hacer push normal
    resultado_push = ejecutar_comando("git push origin main")
    if resultado_push.returncode != 0:
        log("❌ El push normal falló. Intentando con --force...")
        # Intentamos hacer push forzado como último recurso
        resultado_force = ejecutar_comando("git push origin main --force")
        if resultado_force.returncode != 0:
            log("❌ Push forzado también falló. Se requiere intervención manual.")
        else:
            log("✅ Push forzado exitoso.")
    else:
        log("✅ Push exitoso.")

log("📤 Finalizó script de git_push.py\n")
