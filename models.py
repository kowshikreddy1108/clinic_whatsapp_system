from database import db
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

def now_ist():
    return datetime.now(IST)

class PatientLead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100))
    service = db.Column(db.String(100))
    preferred_time = db.Column(db.String(100))
    status = db.Column(db.String(50), default="new")
    stage = db.Column(db.String(50), default="new")
    clinic_notes = db.Column(db.String(300))
    confirmed_time = db.Column(db.String(100))
    confirmed_datetime = db.Column(db.DateTime, nullable=True)
    followup_count = db.Column(db.Integer, default=0)
    last_followup_sent_at = db.Column(db.DateTime(timezone=True))
    patient_reminder_1_sent = db.Column(db.Boolean, default=False)
    patient_reminder_2_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now_ist)
    problem = db.Column(db.String(200))
    cancelled_by = db.Column(db.String(20), nullable=True)