import os
import requests
from dotenv import load_dotenv

load_dotenv()

WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
CLINIC_OWNER_PHONE = os.environ.get("CLINIC_OWNER_PHONE")

BASE_URL = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

HEADERS = {
    "Authorization": f"Bearer {WHATSAPP_TOKEN}",
    "Content-Type": "application/json"
}


def _send(to, message):
    """Core send function. All other functions call this."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    try:
        response = requests.post(BASE_URL, headers=HEADERS, json=payload)
        result = response.json()
        if response.status_code != 200:
            print(f"[WhatsApp] Send failed to {to}: {result}")
        else:
            print(f"[WhatsApp] Sent to {to}: {message[:50]}...")
        return result
    except Exception as e:
        print(f"[WhatsApp] Exception sending to {to}: {e}")
        return None


def send_patient_message(phone, message):
    """Send message to patient."""
    return _send(phone, message)


def send_owner_message(message):
    """Send message to clinic owner."""
    return _send(CLINIC_OWNER_PHONE, message)