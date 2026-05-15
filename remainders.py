# reminders.py

from datetime import datetime, timedelta
from models import Lead
from database import db

def send_whatsapp_message(phone, message):
    # Replace this with your Twilio / WhatsApp sending code
    print(f"Sending to {phone}: {message}")


def check_and_send_reminders(app):
    with app.app_context():
        now = datetime.now()

        # Reminder 30 minutes before appointment
        reminder_time = now + timedelta(minutes=30)

        leads = Lead.query.filter(
            Lead.appointment_time != None,
            Lead.reminder_sent == False,
            Lead.appointment_time <= reminder_time,
            Lead.appointment_time > now
        ).all()

        for lead in leads:
            message = f"Reminder: Your clinic appointment is at {lead.appointment_time.strftime('%I:%M %p')} today."

            send_whatsapp_message(lead.phone, message)

            lead.reminder_sent = True
            db.session.commit()