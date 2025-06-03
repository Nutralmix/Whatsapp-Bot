import requests
from meta_config import ACCESS_TOKEN, PHONE_NUMBER_ID, API_VERSION

def enviar_mensaje(destinatario, mensaje):
    url = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": destinatario,
        "type": "text",
        "text": { "body": mensaje }
    }

    response = requests.post(url, headers=headers, json=payload)
    print("📬 Estado:", response.status_code)
    print("📨 Respuesta:", response.text)

# ✅ Probalo con tu número (¡importante! formato internacional, sin espacios)
enviar_mensaje("5492317571129", "¡Hola Seba! El bot ya está andando con Meta WhatsApp 🚀")
