# reminders.py

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from models import PatientLead
from database import db
from whatsapp import send_patient_message, send_owner_message

IST = ZoneInfo("Asia/Kolkata")


def now_ist():
    return datetime.now(IST)


def check_and_send_reminders(app):
    with app.app_context():
        now = now_ist()

        # Fetch all confirmed appointments where reminders are not fully sent
        leads = PatientLead.query.filter(
            PatientLead.confirmed_datetime != None,
            PatientLead.status == "clinic_confirmed",
            db.or_(
                PatientLead.patient_reminder_1_sent == False,
                PatientLead.patient_reminder_2_sent == False
            )
        ).all()

        for lead in leads:
            # Make confirmed_datetime timezone-aware (IST)
            appt = lead.confirmed_datetime
            if appt.tzinfo is None:
                appt = appt.replace(tzinfo=IST)

            time_until = appt - now

            # â”€â”€ Reminder 1 â€” 24 hours before â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            if (
                not lead.patient_reminder_1_sent
                and timedelta(hours=23, minutes=55) <= time_until <= timedelta(hours=24, minutes=5)
            ):
                message = (
                    f"Hello {lead.name}, this is a reminder from Varadhi Clinic.\n\n"
                    f"Your appointment is tomorrow at {lead.confirmed_time}.\n"
                    f"Please arrive on time. If you need to reschedule, reply here."
                )
                send_patient_message(lead.phone, message)
                lead.patient_reminder_1_sent = True
                db.session.commit()

                print(f"[Reminder 1 - 24hr] Sent to {lead.phone} â€” {lead.name}")

            # â”€â”€ Reminder 2 â€” 1 hour before â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            elif (
                not lead.patient_reminder_2_sent
                and timedelta(minutes=55) <= time_until <= timedelta(minutes=65)
            ):
                message = (
                    f"Hello {lead.name}, your appointment at Varadhi Clinic "
                    f"is in 1 hour at {lead.confirmed_time}.\n\n"
                    f"We look forward to seeing you. Please arrive a few minutes early."
                )
                send_patient_message(lead.phone, message)
                lead.patient_reminder_2_sent = True
                db.session.commit()

                print(f"[Reminder 2 - 1hr] Sent to {lead.phone} â€” {lead.name}")

            # â”€â”€ No-show detection â€” 30 minutes after appointment â”€â”€â”€â”€â”€â”€â”€â”€â”€
            elif (
                lead.patient_reminder_1_sent
                and lead.patient_reminder_2_sent
                and lead.status == "clinic_confirmed"
                and now > appt + timedelta(minutes=30)
            ):
                lead.status = "no_show"
                db.session.commit()

                # Notify owner about no-show
                owner_message = (
                    f"NO-SHOW ALERT\n\n"
                    f"Patient: {lead.name}\n"
                    f"Phone: {lead.phone}\n"
                    f"Appointment was at: {lead.confirmed_time}\n\n"
                    f"They did not arrive. Reply to follow up or reschedule."
                )
                send_owner_message(owner_message)

                # Send recovery message to patient
                recovery_message = (
                    f"Hello {lead.name}, we noticed you missed your appointment "
                    f"at Varadhi Clinic today.\n\n"
                    f"We'd love to help you. Reply here to reschedule at a time "
                    f"that works for you."
                )
                send_patient_message(lead.phone, recovery_message)

                print(f"[No-Show] Flagged and recovery sent to {lead.phone} â€” {lead.name}")
