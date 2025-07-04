from flask import Blueprint, request, render_template, redirect
import os
from global_state import users, save_users, subjects, save_subjects
from werkzeug.utils import secure_filename
from datetime import datetime
import json

admin_routes = Blueprint('admin', __name__)
UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@admin_routes.route('/')
def admin_dashboard():
    pending = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if filename.endswith("_payment.jpg"):
            parts = filename.rsplit("_", 2)
            if len(parts) == 3:
                email = parts[0]
                subject_id = parts[1]
                if email in users and str(subject_id) in users[email].get("paid_subjects", {}):
                    paid_info = users[email]["paid_subjects"][str(subject_id)]
                    if not paid_info.get("approved", False):
                        # ✅ define subject_name before using it
                        subject_name = next((s["name"] for s in subjects if str(s["id"]) == str(subject_id)), "Unknown Subject")
                        pending.append({
                            "email": email,
                            "subject_id": subject_id,
                            "subject_name": subject_name,
                            "screenshot": f"/uploads/{filename}"
                        })

    ANSWERS_FOLDER = os.path.join("uploads", "answers")
    answers_by_subject = {}
    if os.path.exists(ANSWERS_FOLDER):
        for subject in subjects:
            sid = str(subject['id'])
            answers_by_subject[sid] = []
            for filename in os.listdir(ANSWERS_FOLDER):
                if filename.endswith(".pdf") and filename.startswith(f"{sid}_"):
                    parts = filename.split("_", 1)
                    if len(parts) == 2:
                        email = parts[1].replace(".pdf", "")
                        username = users.get(email, {}).get("username", email)
                        answers_by_subject[sid].append({
                            'email': username,
                            'file': f"/uploads/answers/{filename}"
                        })

    return render_template("admin_dashboard.html",
                           pending=pending,
                           subjects=subjects,
                           answers_by_subject=answers_by_subject)


@admin_routes.route('/approve', methods=['POST'])
def approve_user():
    email = request.form.get('email')
    if email in users:
        users[email]['is_subscribed'] = True
        save_users()
    return redirect('/admin')

# ✅ NEW: Approve subject-specific payment
@admin_routes.route('/approve_subject_payment', methods=['POST'])
def approve_subject_payment():
    email = request.form.get('email')
    subject_id = request.form.get('subject_id')

    if email in users and subject_id in users[email].get("paid_subjects", {}):
        users[email]["paid_subjects"][subject_id]["approved"] = True
        save_users()
        return redirect('/admin')
    else:
        return "Invalid data", 400

@admin_routes.route('/upload_key', methods=['POST'])
def upload_answer_key():
    sid = request.form.get('subject_id')
    pdf = request.files.get('key_pdf')

    if not sid or not pdf:
        return 'Missing data', 400

    subject = next((s for s in subjects if str(s['id']) == str(sid)), None)
    if not subject:
        return 'Invalid subject', 400

    filename = f"key_{sid}.pdf"
    KEYS_FOLDER = os.path.join("uploads", "keys")
    os.makedirs(KEYS_FOLDER, exist_ok=True)
    pdf.save(os.path.join(KEYS_FOLDER, filename))

    subject['keys'] = {'file': filename}
    save_subjects()
    return redirect('/admin')

@admin_routes.route('/update_marks', methods=['POST'])
def update_marks():
    email = request.form.get('email')
    sid = request.form.get('subject_id')
    marks = request.form.get('marks')

    subject = next((s for s in subjects if str(s['id']) == str(sid)), None)
    if not subject:
        return 'Invalid subject', 400

    subject.setdefault('marks', {})[email] = marks
    save_subjects()
    return redirect('/admin')

@admin_routes.route('/add_subject', methods=['POST'])
def add_subject():
    name = request.form.get('subject_name')
    qfile = request.files.get('question_file')

    if not name or not qfile:
        return 'Missing data', 400

    QUESTIONS_FOLDER = os.path.join("uploads", "questions")
    os.makedirs(QUESTIONS_FOLDER, exist_ok=True)

    next_id = max([s["id"] for s in subjects], default=0) + 1
    filename = f"{name.lower().replace(' ', '_')}.pdf"
    qfile.save(os.path.join(QUESTIONS_FOLDER, filename))

    new_subject = {
        "id": next_id,
        "name": name,
        "question_file": filename,
        "keys": {},
        "answers": {},
        "marks": {}
    }

    subjects.append(new_subject)
    save_subjects()
    return redirect('/admin')

@admin_routes.route('/delete_subject', methods=['POST'])
def delete_subject():
    sid = request.form.get('subject_id')
    subject = next((s for s in subjects if str(s['id']) == str(sid)), None)

    if not subject:
        return 'Invalid subject', 400

    qfile = subject.get('question_file')
    if qfile:
        qpath = os.path.join('uploads', 'questions', qfile)
        if os.path.exists(qpath):
            os.remove(qpath)

    keyfile = subject.get('keys', {}).get('file')
    if keyfile:
        kpath = os.path.join('uploads', 'keys', keyfile)
        if os.path.exists(kpath):
            os.remove(kpath)

    for email, info in subject.get('answers', {}).items():
        ans_path = os.path.join('uploads', 'answers', info['file'])
        if os.path.exists(ans_path):
            os.remove(ans_path)

    subjects.remove(subject)
    save_subjects()
    return redirect('/admin')

@admin_routes.route('/delete_subject_files', methods=['POST'])
def delete_subject_files():
    sid = request.form.get('subject_id')
    subject = next((s for s in subjects if str(s['id']) == str(sid)), None)

    if not subject:
        return 'Invalid subject', 400

    qfile_path = os.path.join("uploads", "questions", subject['question_file'])
    if os.path.exists(qfile_path):
        os.remove(qfile_path)

    key_file = subject.get("keys", {}).get("file")
    if key_file:
        kfile_path = os.path.join("uploads", "keys", key_file)
        if os.path.exists(kfile_path):
            os.remove(kfile_path)
        subject['keys'] = {}

    subject['question_file'] = ""
    save_subjects()

    return redirect('/admin')

@admin_routes.route("/add_question_to_subject", methods=["POST"])
def add_question_to_subject():
    subject_id = request.form['subject_id']
    question_file = request.files['question_file']

    if not subject_id or not question_file:
        return "Missing subject or file", 400

    questions_dir = os.path.join('uploads', 'questions')
    os.makedirs(questions_dir, exist_ok=True)

    filename = secure_filename(question_file.filename)
    save_path = os.path.join(questions_dir, f"{subject_id}_{filename}")
    question_file.save(save_path)

    relative_path = save_path.replace("\\", "/")

    with open('subjects.json', 'r+', encoding='utf-8') as f:
        subjects = json.load(f)
        for subject in subjects:
            if str(subject['id']) == str(subject_id):
                if 'extra_questions' not in subject:
                    subject['extra_questions'] = []
                subject['extra_questions'].append(relative_path)
                break
        f.seek(0)
        json.dump(subjects, f, indent=2)
        f.truncate()

    return redirect('/admin')