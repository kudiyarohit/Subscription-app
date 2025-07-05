from flask import Blueprint, request, render_template, redirect
from werkzeug.utils import secure_filename
import os
from datetime import datetime

from models import User, Subject, Payment, Answer, Mark
from db import db

admin_routes = Blueprint('admin_routes', __name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ------------------ 🔧 Dashboard ------------------ #
@admin_routes.route('/')
def admin_dashboard():
    # Pending payments
    pending = []
    payments = Payment.query.filter_by(approved=False).all()
    for p in payments:
        subject = Subject.query.filter_by(id=p.subject_id).first()
        user = User.query.filter_by(email=p.user_email).first()
        username = user.username if user and user.username else "Unknown"

        pending.append({
            "email": p.user_email,
            "username": username,
            "subject_id": p.subject_id,
            "subject_name": subject.name if subject else "Unknown",
            "screenshot": f"/uploads/{p.screenshot_filename}"
        })

    # Uploaded answers
    answers_by_subject = {}
    subjects = Subject.query.all()
    for subject in subjects:
        sid = str(subject.id)
        answers_by_subject[sid] = []
        answers = Answer.query.filter_by(subject_id=sid).all()
        for a in answers:
            user = User.query.filter_by(email=a.user_email).first()
            username = user.username if user and user.username else a.user_email
            answers_by_subject[sid].append({
                'email': username,
                'file': f"/uploads/answers/{a.file_name}"
            })

    return render_template("admin_dashboard.html",
                           pending=pending,
                           subjects=subjects,
                           answers_by_subject=answers_by_subject)


# ------------------ ✅ Approve Subject Payment ------------------ #
@admin_routes.route('/approve_subject_payment', methods=['POST'])
def approve_subject_payment():
    email = request.form.get('email')
    subject_id = request.form.get('subject_id')

    payment = Payment.query.filter_by(user_email=email, subject_id=subject_id).first()
    if payment:
        # ✅ Delete screenshot file
        if payment.screenshot_filename:
            path = os.path.join('uploads', payment.screenshot_filename)
            if os.path.exists(path):
                os.remove(path)

        # ✅ Clear screenshot field if needed (optional)
        # payment.screenshot_filename = None

        payment.approved = True
        db.session.commit()
        return redirect('/admin')

    return "Invalid data", 400


# ------------------ 🔑 Upload Answer Key ------------------ #
@admin_routes.route('/upload_key', methods=['POST'])
def upload_answer_key():
    sid = request.form.get('subject_id')
    pdf = request.files.get('key_pdf')

    if not sid or not pdf:
        return 'Missing data', 400

    filename = f"key_{sid}.pdf"
    KEYS_FOLDER = os.path.join("uploads", "keys")
    os.makedirs(KEYS_FOLDER, exist_ok=True)
    pdf.save(os.path.join(KEYS_FOLDER, filename))

    subject = Subject.query.filter_by(id=sid).first()
    if subject:
        subject.key_file = filename
        db.session.commit()
        return redirect('/admin')
    return 'Invalid subject', 400


# ------------------ 🎯 Update Marks ------------------ #
@admin_routes.route('/update_marks', methods=['POST'])
def update_marks():
    email = request.form.get('email')
    sid = request.form.get('subject_id')
    marks = request.form.get('marks')

    mark = Mark.query.filter_by(user_email=email, subject_id=sid).first()
    if mark:
        mark.score = marks
    else:
        mark = Mark(user_email=email, subject_id=sid, score=marks)
        db.session.add(mark)

    db.session.commit()
    return redirect('/admin')


# ------------------ ➕ Add Subject ------------------ #
@admin_routes.route('/add_subject', methods=['POST'])
def add_subject():
    name = request.form.get('subject_name')
    qfile = request.files.get('question_file')

    if not name or not qfile:
        return 'Missing data', 400

    QUESTIONS_FOLDER = os.path.join("uploads", "questions")
    os.makedirs(QUESTIONS_FOLDER, exist_ok=True)

    filename = secure_filename(qfile.filename)
    qfile.save(os.path.join(QUESTIONS_FOLDER, filename))

    new_subject = Subject(name=name, question_file=filename)
    db.session.add(new_subject)
    db.session.commit()

    return redirect('/admin')


# ------------------ ❌ Delete Subject ------------------ #
@admin_routes.route('/delete_subject', methods=['POST'])
def delete_subject():
    sid = request.form.get('subject_id')
    subject = Subject.query.filter_by(id=sid).first()

    if not subject:
        return 'Invalid subject', 400

    # Delete files
    if subject.question_file:
        qpath = os.path.join('uploads', 'questions', subject.question_file)
        if os.path.exists(qpath): os.remove(qpath)

    if subject.key_file:
        kpath = os.path.join('uploads', 'keys', subject.key_file)
        if os.path.exists(kpath): os.remove(kpath)

    # Delete subject & related answers/marks/payments
    Answer.query.filter_by(subject_id=sid).delete()
    Mark.query.filter_by(subject_id=sid).delete()
    Payment.query.filter_by(subject_id=sid).delete()
    db.session.delete(subject)
    db.session.commit()

    return redirect('/admin')


# ------------------ 🔁 Replace Question File ------------------ #
@admin_routes.route("/add_question_to_subject", methods=["POST"])
def add_question_to_subject():
    subject_id = request.form['subject_id']
    question_file = request.files['question_file']

    if not subject_id or not question_file:
        return "Missing subject or file", 400

    subject = Subject.query.filter_by(id=subject_id).first()
    if not subject:
        return "Invalid subject", 400

    # ✅ Remove old file if it exists
    if subject.question_file:
        old_path = os.path.join('uploads', 'questions', subject.question_file)
        if os.path.exists(old_path):
            os.remove(old_path)

    # ✅ Save new file
    questions_dir = os.path.join('uploads', 'questions')
    os.makedirs(questions_dir, exist_ok=True)

    filename = secure_filename(question_file.filename)
    saved_filename = f"{subject_id}_{filename}"
    question_file.save(os.path.join(questions_dir, saved_filename))

    subject.question_file = saved_filename
    db.session.commit()

    return redirect('/admin')

@admin_routes.route('/delete_question_file', methods=['POST'])
def delete_question_file():
    subject_id = request.form.get('subject_id')
    subject = Subject.query.filter_by(id=subject_id).first()

    if not subject or not subject.question_file:
        return 'Invalid subject or no question file', 400

    qpath = os.path.join('uploads', 'questions', subject.question_file)
    if os.path.exists(qpath):
        os.remove(qpath)

    subject.question_file = None
    db.session.commit()
    return redirect('/admin')

@admin_routes.route('/delete_key_file', methods=['POST'])
def delete_key_file():
    subject_id = request.form.get('subject_id')
    subject = Subject.query.filter_by(id=subject_id).first()

    if not subject or not subject.key_file:
        return 'Invalid subject or no key file', 400

    kpath = os.path.join('uploads', 'keys', subject.key_file)
    if os.path.exists(kpath):
        os.remove(kpath)

    subject.key_file = None
    db.session.commit()
    return redirect('/admin')
