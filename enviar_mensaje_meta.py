import requests
from meta_config import ACCESS_TOKEN, PHONE_NUMBER_ID, API_VERSION

def enviar_mensaje(destinatario, mensaje):
    """Envía un mensaje de texto por WhatsApp utilizando la API de Meta."""
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

    try:
        response = requests.post(url, headers=headers, json=payload)
        print("📬 Estado:", response.status_code)
        print("📨 Respuesta:", response.text)
    except requests.exceptions.RequestException as e:
        print("❌ Error al enviar el mensaje:", e)

# --- PRUEBA MANUAL ---
if __name__ == "__main__":
    # Solo se ejecuta si corres este archivo directamente
    numero_prueba = "5492317571129"  # Reemplazar si querés probar con otro número
    mensaje_prueba = "¡Hola Seba! El bot ya está andando con Meta WhatsApp 🚀"
    enviar_mensaje(numero_prueba, mensaje_prueba)
