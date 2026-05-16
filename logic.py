import requests
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

from dotenv import load_dotenv
from twilio.rest import Client
account_sid = ""
auth_token = ""

client = Client(account_sid, auth_token)





def now_ist():
    return datetime.now(IST)


def send_telegram_notification(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    response = requests.post(url, data=payload)

    print("Telegram status:", response.status_code)
    print("Telegram response:", response.text)

    return response


def send_patient_whatsapp_message(phone, message):
     client.messages.create(
        body=message,
        from_="whatsapp:",  # Twilio sandbox number
        to=f"whatsapp:{phone}"
    )


def process_message(patient, text):
    text = text.strip().lower()

    handoff_words = [
        "doctor", "call", "urgent", "emergency", "staff",
        "human", "reception", "pain", "serious", "immediate",
        "talk", "speak", "help"
    ]

    if any(word in text for word in handoff_words):
        patient.status = "human_handoff"
        patient.stage = "human_handoff"

        notification = (
            f"URGENT HUMAN HANDOFF NEEDED\n\n"
            f"Phone: {patient.phone}\n"
            f"Name: {patient.name if patient.name else 'Not collected yet'}\n"
            f"Service: {patient.service if patient.service else 'Not collected yet'}\n"
            f"Message: {text}\n\n"
            f"Please contact this patient immediately."
        )

        send_telegram_notification(notification)

        return "Our clinic team has been notified. They will contact you shortly."

    if patient.stage == "new":
        patient.stage = "asked_name"

        return (
            "Hi, thanks for contacting Varadhi Clinic.\n"
            "Please enter your full name."
        )

    elif patient.stage == "asked_name":
        patient.name = text.title()
        patient.stage = "asked_service"

        return (
            "What service do you need?\n"
            "1. Dental checkup\n"
            "2. Skin consultation\n"
            "3. Physiotherapy\n"
            "4. Other"
        )

    elif patient.stage == "asked_service":
        services = {
            "1": "Dental checkup",
            "2": "Skin consultation",
            "3": "Physiotherapy",
            "4": "Other"
        }

        patient.service = services.get(text, text.title())
        patient.stage = "asked_time"

        return "Please enter your preferred appointment date and time."

    elif patient.stage == "asked_time":
        patient.preferred_time = text
        patient.stage = "completed"
        patient.status = "appointment_requested"
        patient.last_followup_sent_at = now_ist()

        notification = (
    f"NEW CLINIC ENQUIRY\n\n"
    f"Patient ID: {patient.id}\n"
    f"Name: {patient.name}\n"
    f"Phone: {patient.phone}\n"
    f"Service: {patient.service}\n"
    f"Preferred Time: {patient.preferred_time}\n\n"

   f"REPLY IN THESE EXACT FORMAT:\n\n"

    f"1)To confirm:(if the appoinment is confirmed)\n"
    f"  id={patient.id},time=29-04-2026 06:30 PM\n\n"

    f"2)To cancel:(if the appointment is cancelled)\n"
    f"  id={patient.id},cancel\n\n\n"


    f"\n ❌ Do NOT send vague text like 'tomorrow', 'evening'"
)

        send_telegram_notification(notification)

        return (
            f"Thank you {patient.name}, your request has been received.\n"
            f"Our clinic will contact you shortly."
        )

    else:
        return "Thanks. Our clinic team will contact you shortly."
