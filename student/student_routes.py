from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import datetime, os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
student_routes = Blueprint('student_routes', __name__)

from global_state import users, subjects, save_subjects, get_subjects_for_user, save_users

def get_email_from_token(token):
    try:
        import jwt
        from dotenv import load_dotenv
        load_dotenv()
        SECRET_KEY = os.getenv("SECRET_KEY")
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded['email']
    except:
        return None

def find_subject(sid):
    return next((s for s in subjects if str(s['id']) == str(sid)), None)

@student_routes.route('/subjects', methods=['GET'])
def list_subjects():
    token = request.headers.get('Authorization')
    email = get_email_from_token(token)
    if not email or email not in users:
        return jsonify({"error": "Unauthorized"}), 401

    return jsonify(get_subjects_for_user(email))

# ✅ New: Upload subject-specific payment screenshot
@student_routes.route('/pay_subject', methods=['POST'])
def pay_subject():
    token = request.headers.get('Authorization')
    email = get_email_from_token(token)
    if not email or email not in users:
        return jsonify({"error": "Unauthorized"}), 401

    subject_id = request.form.get('subject_id')
    screenshot = request.files.get('screenshot')
    if not subject_id or not screenshot:
        return jsonify({"error": "Missing subject_id or screenshot"}), 400

    os.makedirs("uploads", exist_ok=True)
    filename = f"{email}_{subject_id}_payment.jpg"
    screenshot.save(os.path.join("uploads", filename))

    users[email].setdefault("paid_subjects", {})[str(subject_id)] = {
        "approved": False,
        "screenshot": filename
    }
    save_users()
    return jsonify({"message": "Payment screenshot uploaded"}), 200

from flask import current_app
import smtplib

# Optional email notification
def notify_admin_upload(email, subject_name):
    try:
        sender = os.getenv("EMAIL")
        password = os.getenv("PASSWORD")
        admin = os.getenv("ADMIN_EMAIL")
        msg = f"Subject: New Answer Uploaded\\n\\nStudent {email} uploaded an answer for '{subject_name}'."

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, admin, msg)
    except Exception as e:
        print(f"❌ Failed to notify admin: {e}")

@student_routes.route('/upload', methods=['POST'])
def upload_answer_fallback():
    token = request.headers.get('Authorization')
    email = get_email_from_token(token)
    if not email:
        return jsonify({"error": "Unauthorized"}), 401

    subject_id = request.form.get('subject_id')
    pdf = request.files.get('answer_pdf')
    if not subject_id or not pdf:
        return jsonify({"error": "Missing subject_id or file"}), 400

    # ✅ Check per-subject payment approval
    if email not in users or str(subject_id) not in users[email].get("paid_subjects", {}) \
            or not users[email]["paid_subjects"][str(subject_id)]["approved"]:
        return jsonify({"error": "Payment not approved"}), 403

    subject = find_subject(subject_id)
    if not subject:
        return jsonify({"error": "Invalid subject"}), 400

    ANSWERS_FOLDER = os.path.join('uploads', 'answers')
    os.makedirs(ANSWERS_FOLDER, exist_ok=True)
    filename = secure_filename(f"{subject_id}_{email}.pdf")
    filepath = os.path.join(ANSWERS_FOLDER, filename)
    pdf.save(filepath)

    subject.setdefault('answers', {})[email] = {
        'file': filename,
        'time': datetime.datetime.utcnow().isoformat()
    }

    save_subjects()
    notify_admin_upload(email, subject['name'])
    return jsonify({"message": "Answer uploaded successfully"}), 200
