from datetime import datetime
from models import PatientLead
from database import db
from whatsapp import send_patient_message, send_owner_message
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def handle_owner_reply(text):
    text = text.strip()

    # Expected formats:
    # id=2,cancel
    # id=2,time=29-04-2026 06:30 PM

    try:
        id_part, action_part = text.split(",", 1)
        patient_id = int(id_part.replace("id=", "").strip())
        patient = PatientLead.query.get(patient_id)

        if not patient:
            send_owner_message("Patient not found. Check the ID and try again.")
            return

    except Exception:
        send_owner_message(
            "Invalid format.\n\n"
            "To confirm appointment:\n"
            "id=2,time=29-04-2026 06:30 PM\n\n"
            "To cancel appointment:\n"
            "id=2,cancel"
        )
        return

    action = action_part.strip().lower()

    # CANCEL
    if action == "cancel":
        patient.status = "cancelled"
        patient.clinic_notes = "Cancelled by clinic"
        patient.patient_reminder_1_sent = True
        patient.patient_reminder_2_sent = True
        patient.cancelled_by = "clinic"
        db.session.commit()

        send_patient_message(
            patient.phone,
            "Your appointment request at Varadhi Clinic has been cancelled.\n"
            "If you want to book another slot, please message us again."
        )
        send_owner_message(
            f"Cancelled successfully.\n\n"
            f"Patient: {patient.name}\n"
            f"Phone: {patient.phone}\n\n"
            f"Patient has been notified."
        )
        return

    # CONFIRM
    if action.startswith("time="):
        confirmed_time = action_part.strip()[5:].strip()

        try:
            confirmed_datetime = datetime.strptime(
                confirmed_time, "%d-%m-%Y %I:%M %p"
            )
        except ValueError:
            send_owner_message(
                "Wrong time format.\n\n"
                "Use exactly this format:\n"
                "id=2,time=29-04-2026 06:30 PM"
            )
            return

        patient.status = "clinic_confirmed"
        patient.confirmed_time = confirmed_time
        patient.confirmed_datetime = confirmed_datetime
        patient.patient_reminder_1_sent = False
        patient.patient_reminder_2_sent = False
        db.session.commit()

        send_patient_message(
            patient.phone,
            f"Your appointment at Varadhi Clinic is confirmed.\n"
            f"Date and Time: {confirmed_time}\n"
            f"You will receive reminders before your appointment."
        )
        send_owner_message(
            f"Appointment confirmed.\n\n"
            f"Patient: {patient.name}\n"
            f"Phone: {patient.phone}\n"
            f"Time: {confirmed_time}\n\n"
            f"Patient has been notified."
        )
        return

    # Unknown command
    send_owner_message(
        "Did not understand that.\n\n"
        "To confirm: id=2,time=29-04-2026 06:30 PM\n"
        "To cancel: id=2,cancel"
    )