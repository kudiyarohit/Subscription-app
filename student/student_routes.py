from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
import os, smtplib
from dotenv import load_dotenv

from db import db
from models import User, Subject, Payment, Answer, Mark
from flask_jwt_extended import jwt_required, get_jwt_identity

student_routes = Blueprint('student_routes', __name__)
load_dotenv()

# ----------------- 📚 Get Subjects ----------------- #
@student_routes.route('/subjects', methods=['GET'])
@jwt_required()
def get_subjects():
    email = get_jwt_identity()
    user = User.query.get(email)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    all_subjects = Subject.query.all()
    result = []

    for subject in all_subjects:
        answer = Answer.query.filter_by(user_email=email, subject_id=subject.id).first()
        payment = Payment.query.filter_by(user_email=email, subject_id=subject.id, approved=True).first()
        mark = Mark.query.filter_by(user_email=email, subject_id=subject.id).first()

        result.append({
            'id': subject.id,
            'name': subject.name,
            'question_file': f"/files/questions/{subject.question_file}" if subject.question_file else None,
            'answer_uploaded': bool(answer),
            'paid_subjects': bool(payment),
            'approved': bool(payment),
            'marks': mark.score if mark else None,
            'key_ready': bool(subject.key_file),
            'answer_key': f"/files/keys/{subject.key_file}" if subject.key_file else None,
        })

    return jsonify(result), 200


# ----------------- 💰 Pay for Subject ----------------- #
@student_routes.route('/pay_subject', methods=['POST'])
@jwt_required()
def pay_subject():
    email = get_jwt_identity()
    subject_id = request.form.get('subject_id')
    screenshot = request.files.get('screenshot')

    if not subject_id or not screenshot:
        return jsonify({"error": "Missing subject_id or screenshot"}), 400

    filename = f"{email}_{subject_id}_payment.jpg"
    os.makedirs("uploads", exist_ok=True)
    screenshot.save(os.path.join("uploads", filename))

    payment = Payment.query.filter_by(user_email=email, subject_id=subject_id).first()
    if payment:
        payment.screenshot_filename = filename
        payment.approved = False
    else:
        payment = Payment(user_email=email, subject_id=subject_id, screenshot_filename=filename, approved=False)
        db.session.add(payment)

    db.session.commit()
    return jsonify({"message": "Payment screenshot uploaded"}), 200


# ----------------- 📤 Upload Answer ----------------- #
@student_routes.route('/upload', methods=['POST'])
@jwt_required()
def upload_answer():
    email = get_jwt_identity()
    subject_id = request.form.get('subject_id')
    pdf = request.files.get('answer_pdf')

    if not subject_id or not pdf:
        return jsonify({"error": "Missing subject_id or file"}), 400

    payment = Payment.query.filter_by(user_email=email, subject_id=subject_id, approved=True).first()
    if not payment:
        return jsonify({"error": "Payment not approved"}), 403

    subject = Subject.query.filter_by(id=subject_id).first()
    if not subject:
        return jsonify({"error": "Invalid subject"}), 400

    ANSWERS_FOLDER = os.path.join('uploads', 'answers')
    os.makedirs(ANSWERS_FOLDER, exist_ok=True)
    filename = secure_filename(f"{subject_id}_{email}.pdf")
    filepath = os.path.join(ANSWERS_FOLDER, filename)
    pdf.save(filepath)

    answer = Answer.query.filter_by(user_email=email, subject_id=subject_id).first()
    if answer:
        answer.file_name = filename
        answer.submitted_at = datetime.utcnow()
    else:
        answer = Answer(user_email=email, subject_id=subject_id, file_name=filename)
        db.session.add(answer)

    db.session.commit()
    notify_admin_upload(email, subject.name)
    return jsonify({"message": "Answer uploaded successfully"}), 200


# ----------------- ✉️ Optional Email Notification ----------------- #
def notify_admin_upload(email, subject_name):
    try:
        sender = os.getenv("EMAIL")
        password = os.getenv("PASSWORD")
        admin = os.getenv("ADMIN_EMAIL")
        msg = f"Subject: New Answer Uploaded\n\nStudent {email} uploaded an answer for '{subject_name}'."

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, admin, msg)
    except Exception as e:
        print(f"❌ Failed to notify admin: {e}")
