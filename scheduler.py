from datetime import datetime
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
from models import PatientLead
from database import db
from whatsapp import send_patient_message, send_owner_message

IST = ZoneInfo("Asia/Kolkata")


def now_ist():
    return datetime.now(IST)


def clinic_followup_job(app):
    with app.app_context():
        patients = PatientLead.query.filter_by(
            status="appointment_requested"
        ).all()

        for patient in patients:
            if patient.followup_count >= 3:
                continue

            if not patient.last_followup_sent_at:
                patient.last_followup_sent_at = now_ist()
                db.session.commit()
                continue

            last_time = patient.last_followup_sent_at
            if last_time.tzinfo is None:
                last_time = last_time.replace(tzinfo=IST)

            elapsed = (now_ist() - last_time).total_seconds()

            if elapsed > 1800:
                send_owner_message(
                    f"Follow-up needed ({patient.followup_count + 1}/3)\n\n"
                    f"Patient is waiting for confirmation.\n\n"
                    f"Name: {patient.name}\n"
                    f"Phone: {patient.phone}\n"
                    f"Service: {patient.service}\n"
                    f"Preferred Time: {patient.preferred_time}\n\n"
                    f"Reply to confirm:\n"
                    f"id={patient.id},time=DD-MM-YYYY HH:MM AM/PM\n\n"
                    f"Reply to cancel:\n"
                    f"id={patient.id},cancel"
                )
                patient.followup_count += 1
                patient.last_followup_sent_at = now_ist()
                db.session.commit()


def patient_reminder_job(app):
    with app.app_context():
        now = datetime.now()
        patients = PatientLead.query.filter_by(
            status="clinic_confirmed"
        ).all()

        for patient in patients:
            if not patient.confirmed_datetime:
                continue

            time_left = (patient.confirmed_datetime - now).total_seconds()

            # 3 hours before
            if 0 < time_left <= 10800 and not patient.patient_reminder_1_sent:
                send_patient_message(
                    patient.phone,
                    f"Reminder: Your appointment at Varadhi Clinic is in 3 hours.\n"
                    f"Time: {patient.confirmed_time}\n"
                    f"Please be on time."
                )
                patient.patient_reminder_1_sent = True
                db.session.commit()

            # 30 minutes before
            if 0 < time_left <= 1800 and not patient.patient_reminder_2_sent:
                send_patient_message(
                    patient.phone,
                    f"Final reminder: Your appointment at Varadhi Clinic is in 30 minutes.\n"
                    f"Time: {patient.confirmed_time}"
                )
                patient.patient_reminder_2_sent = True
                db.session.commit()


def start_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        clinic_followup_job, 'interval',
        minutes=1, args=[app]
    )
    scheduler.add_job(
        patient_reminder_job, 'interval',
        minutes=1, args=[app]
    )
    scheduler.start()
    print("[Scheduler] Background jobs started.")
    return scheduler