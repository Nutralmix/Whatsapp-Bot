from dotenv import load_dotenv
import os

load_dotenv()  # Carga las variables de entorno desde .env

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER")
API_VERSION = os.getenv("API_VERSION")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")  # 👈 ESTA LÍNEA AGREGALE
