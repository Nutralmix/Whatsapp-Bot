import subprocess
from datetime import datetime

def auto_push_archivos():
    print("🌀 Subiendo archivos nuevos a Git...")

    try:
        subprocess.run("git add static/archivos", check=True, shell=True)

        status = subprocess.run("git status --porcelain", capture_output=True, text=True, shell=True)
        if not status.stdout.strip():
            print("🟡 No hay cambios nuevos para subir a Git.")
            return

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        mensaje = f"Auto-push desde el panel - {fecha}"
        subprocess.run(f'git commit -m "{mensaje}"', check=True, shell=True)
        subprocess.run("git push origin main", check=True, shell=True)

        print("✅ Cambios subidos a GitHub correctamente.")
    except subprocess.CalledProcessError as e:
        print("❌ Error al ejecutar comando Git:", e)
