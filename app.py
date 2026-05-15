from flask import Flask, request, jsonify
from database import db
from models import PatientLead
from whatsapp import send_patient_message, send_owner_message
from owner_handler import handle_owner_reply
from scheduler import start_scheduler
from logic import process_message
from datetime import datetime
from zoneinfo import ZoneInfo
import os
from dotenv import load_dotenv

load_dotenv()

IST = ZoneInfo("Asia/Kolkata")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///clinic.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

OWNER_PHONE = os.environ.get("CLINIC_OWNER_PHONE")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")


def format_time(dt):
    if not dt:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def now_ist():
    return datetime.now(IST)


# ─── Meta webhook verification ───────────────────────────────────────────────

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """Meta calls this once to verify your webhook URL."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("[Webhook] Verified by Meta.")
        return challenge, 200
    return "Forbidden", 403


# ─── Incoming messages ────────────────────────────────────────────────────────

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        # Ignore status updates (delivered, read receipts)
        if "statuses" in value:
            return jsonify({"status": "ignored"}), 200

        message = value["messages"][0]
        phone = message["from"]
        text = message.get("text", {}).get("body", "").strip()

        if not text:
            return jsonify({"status": "no_text"}), 200

    except (KeyError, IndexError):
        return jsonify({"status": "ignored"}), 200

    # Owner reply
    if phone == OWNER_PHONE:
        with app.app_context():
            handle_owner_reply(text)
        return jsonify({"status": "owner_handled"}), 200

    # Patient message
    patient = PatientLead.query.filter_by(phone=phone).first()
    if not patient:
        patient = PatientLead(phone=phone)
        db.session.add(patient)
        db.session.commit()

    reply = process_message(patient, text)
    send_patient_message(phone, reply)
    db.session.commit()

    return jsonify({"status": "ok"}), 200


# ─── Admin routes ─────────────────────────────────────────────────────────────

@app.route("/")
def home():
    return "Varadhi Clinic WhatsApp System Running"


@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": format_time(now_ist())})


@app.route("/patients", methods=["GET"])
def get_patients():
    patients = PatientLead.query.all()
    return jsonify([{
        "id": p.id,
        "phone": p.phone,
        "name": p.name,
        "service": p.service,
        "preferred_time": p.preferred_time,
        "status": p.status,
        "stage": p.stage,
        "confirmed_time": p.confirmed_time,
        "followup_count": p.followup_count,
        "patient_reminder_1_sent": p.patient_reminder_1_sent,
        "patient_reminder_2_sent": p.patient_reminder_2_sent,
        "created_at": format_time(p.created_at)
    } for p in patients])


@app.route("/patients/<int:id>", methods=["GET"])
def get_patient(id):
    p = PatientLead.query.get(id)
    if not p:
        return jsonify({"error": "Not found"}), 404
    return jsonify({
        "id": p.id,
        "phone": p.phone,
        "name": p.name,
        "service": p.service,
        "preferred_time": p.preferred_time,
        "status": p.status,
        "stage": p.stage,
        "confirmed_time": p.confirmed_time,
        "followup_count": p.followup_count,
        "clinic_notes": p.clinic_notes,
        "patient_reminder_1_sent": p.patient_reminder_1_sent,
        "patient_reminder_2_sent": p.patient_reminder_2_sent,
        "created_at": format_time(p.created_at)
    })


# ─── Startup ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    start_scheduler(app)
    app.run(debug=False, port=5000)