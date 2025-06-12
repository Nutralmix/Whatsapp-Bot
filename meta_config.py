from dotenv import load_dotenv
import os

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
API_VERSION = os.getenv("API_VERSION")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
BASE_URL = os.getenv("BASE_URL", "https://whatsapp-bot-1wj3.onrender.com")

