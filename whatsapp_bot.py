from flask import Flask, request
from bot import (
    obtener_usuario_por_telefono,
    procesar_opcion_admin,
    procesar_opcion_empleado,
    obtener_info_empleado_por_nombre_o_id,
    mostrar_menu_admin,
    mostrar_menu_empleado,
    registrar_log,
    guardar_archivo_enviado_por_whatsapp
)
import subprocess
import requests
import json
import os
from datetime import datetime
from meta_config import ACCESS_TOKEN, PHONE_NUMBER_ID, API_VERSION, VERIFY_TOKEN

app = Flask(__name__)
user_states = {}
BASE_URL = os.getenv("BASE_URL", "https://whatsapp-bot-1wj3.onrender.com")

def limpiar_numero(numero):
    numero = numero.replace("+", "")
    if numero.startswith("54"):
        numero = numero[2:]
    if numero.startswith("9"):
        numero = numero[1:]
    return numero

def descargar_media_con_curl(media_url, token, filename_destino):
    comando = [
        "curl", "-L",
        "-H", f"Authorization: Bearer {token}",
        media_url,
        "-o", filename_destino
    ]
    resultado = subprocess.run(comando, capture_output=True)
    print("📄 CURL STDOUT:", resultado.stdout.decode())
    print("⚠️ CURL STDERR:", resultado.stderr.decode())
    return resultado.returncode == 0

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ Webhook verificado correctamente.")
            return challenge, 200
        print("❌ Verificación de webhook fallida.")
        return "Invalid verification", 403

    if request.method == "POST":
        data = request.get_json()
        print("📥 LLEGÓ UN MENSAJE POST:")
        print(json.dumps(data, indent=2))

        try:
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    if "messages" in value:
                        mensaje = value["messages"][0]
                        from_number = limpiar_numero(mensaje["from"])
                        print(f"📲 Mensaje desde: {from_number}")

                        if "image" in mensaje or "document" in mensaje:
                            tipo = "image" if "image" in mensaje else "document"
                            media = mensaje[tipo]
                            media_id = media.get("id")
                            filename = media.get("filename", f"{media_id}.bin")
                            mime_type = media.get("mime_type", "")

                            print(f"📎 Recibido archivo tipo: {tipo} - ID: {media_id} - Nombre: {filename} - MIME: {mime_type}")

                            url_media_info = f"https://graph.facebook.com/{API_VERSION}/{media_id}"
                            headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

                            res_url = requests.get(url_media_info, headers=headers)
                            print(f"🌐 Media info → {res_url.status_code} - {res_url.text}")

                            if res_url.status_code == 200:
                                media_url = res_url.json().get("url")
                                ruta_local = f"./temp/{media_id}.bin"
                                os.makedirs("./temp", exist_ok=True)

                                if descargar_media_con_curl(media_url, ACCESS_TOKEN, ruta_local):
                                    r = guardar_archivo_enviado_por_whatsapp(from_number, ruta_local, mime_type, filename)
                                    enviar_mensaje(from_number, r)
                                else:
                                    enviar_mensaje(from_number, "❌ No se pudo descargar el archivo con curl.")
                            else:
                                enviar_mensaje(from_number, f"❌ No se pudo obtener la URL del archivo (status {res_url.status_code}).")
                            return "OK", 200

                        texto = mensaje.get("text", {}).get("body", "")
                        procesar_mensaje(texto, from_number)

        except Exception as e:
            print("❌ Error al procesar POST:", e)
        return "OK", 200

def procesar_mensaje(texto, from_number):
    texto = texto.strip().lower()
    usuario = obtener_usuario_por_telefono(from_number)
    print(f"💬 Mensaje de {from_number}: '{texto}'")
    print("👤 Usuario identificado:", usuario)

    if from_number not in user_states:
        user_states[from_number] = {"estado": None, "data": {}}
    estado = user_states[from_number]["estado"]

    if not usuario:
        enviar_mensaje(from_number, "❌ No estás registrado. Pedí acceso al administrador.")
        registrar_log({"telefono": from_number, "nombre": "No Registrado"}, f"Intento sin registro: {texto}")
        return

    if texto in ["hola", "menu", "empezar"]:
        if usuario["rol"] == "admin":
            respuesta = mostrar_menu_admin(usuario["nombre"], from_number)
            user_states[from_number]["estado"] = "menu_admin"
        else:
            respuesta = mostrar_menu_empleado(usuario["nombre"], from_number)
            user_states[from_number]["estado"] = "menu_empleado"
        registrar_log(usuario, "📋 Entró al menú principal")
        enviar_mensaje(from_number, respuesta)
        return
    
    if texto == "archivos publicos":
        respuesta = listar_archivos_publicos()
        registrar_log(usuario, "📂 Vió archivos públicos")
        enviar_mensaje(from_number, respuesta)
        return

    if texto == "cancelar":
        user_states[from_number] = {"estado": None, "data": {}}
        menu = mostrar_menu_admin(usuario["nombre"], from_number) if usuario["rol"] == "admin" else mostrar_menu_empleado(usuario["nombre"], from_number)
        enviar_mensaje(from_number, f"🛑 Operación cancelada.\n{menu}")
        registrar_log(usuario, "⛔ Canceló operación")
        return

    if estado in ["menu_admin", "menu_empleado"] and texto.isdigit():
        if usuario["rol"] == "admin":
            respuesta, nuevo_estado = procesar_opcion_admin(usuario, texto, estado, BASE_URL)
        else:
            respuesta, nuevo_estado = procesar_opcion_empleado(usuario, texto, BASE_URL)
        user_states[from_number]["estado"] = nuevo_estado or estado
        registrar_log(usuario, f"Seleccionó opción {texto}")
        enviar_mensaje(from_number, respuesta)
        return

    if estado == "esperando_nombre_info_empleado":
        respuesta = obtener_info_empleado_por_nombre_o_id(texto)
        user_states[from_number] = {"estado": "menu_admin", "data": {}}
        respuesta += "\n" + mostrar_menu_admin(usuario["nombre"], from_number)
        registrar_log(usuario, f"Consultó info de: {texto}")
        enviar_mensaje(from_number, respuesta)
        return

    enviar_mensaje(from_number, "🤖 No entendí tu mensaje. Escribí 'menu' para ver opciones.")
    registrar_log(usuario, f"Mensaje no reconocido: {texto}")

def enviar_mensaje(numero, texto):
    url = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }
    r = requests.post(url, headers=headers, json=payload)
    print(f"➡️ Enviado a {numero}: {texto}")
    print("📨", r.status_code, r.text)
    
def listar_archivos_publicos():
    carpeta = os.path.join("static", "archivos", "publicos")
    if not os.path.exists(carpeta):
        return "📁 No hay archivos públicos disponibles."

    archivos = os.listdir(carpeta)
    if not archivos:
        return "📁 No hay archivos públicos aún."

    mensaje = "📂 Archivos públicos disponibles:\n\n"
    for nombre in archivos:
        url = f"{BASE_URL}/static/archivos/publicos/{nombre}"
        mensaje += f"📎 {nombre}\n🔗 {url}\n\n"
    return mensaje.strip()
   

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
