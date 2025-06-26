import subprocess
from datetime import datetime

def ejecutar_comando(comando):
    resultado = subprocess.run(comando, capture_output=True, text=True, shell=True)
    if resultado.stdout:
        print("✅ STDOUT:", resultado.stdout.strip())
    if resultado.stderr:
        print("⚠️ STDERR:", resultado.stderr.strip())

# Agregar todos los archivos modificados
ejecutar_comando("git add .")

# Commit con fecha y hora
fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M")
mensaje_commit = f"Actualización automática - {fecha_hora}"
ejecutar_comando(f'git commit -m "{mensaje_commit}"')

# Push a main
ejecutar_comando("git push origin main")
