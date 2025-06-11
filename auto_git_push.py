import subprocess
from datetime import datetime

def auto_push_archivos():
    """
    - Agrega cambios en static/archivos/
    - Crea commit automático
    - Hace push a origin/main
    """

    cmds = [
        ["git", "add", "static/archivos/"],
        ["git", "add", "-u", "static/archivos/"],
        ["git", "commit", "-m", f"Auto-push desde panel {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"],
        ["git", "push", "origin", "main"]
    ]
    
    for cmd in cmds:
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print("✅", " ".join(cmd))
            print(res.stdout)
        except subprocess.CalledProcessError as e:
            # Si no hay cambios (commit sale con código 1), lo ignoramos
            if "nothing to commit" in e.stdout.lower() or "nothing to commit" in e.stderr.lower():
                print("ℹ️ Nada que commitear:", e.stdout.strip(), e.stderr.strip())
                return
            print(f"❌ Error en comando: {' '.join(cmd)}")
            print("stdout:", e.stdout)
            print("stderr:", e.stderr)
            return
