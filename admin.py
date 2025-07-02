from flask import Blueprint, request, render_template, redirect
import os
from global_state import users, save_users, subjects, save_subjects

admin_routes = Blueprint('admin', __name__)
UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@admin_routes.route('/')
def admin_dashboard():
    pending = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if filename.endswith("_payment.jpg"):
            email = filename.replace('_payment.jpg', '')
            if email in users and not users[email]['is_subscribed']:
                pending.append((email, f"/uploads/{filename}"))

    # Gather submitted answers
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
                        answers_by_subject[sid].append({
                            'email': email,
                            'file': f"/files/answers/{filename}"
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
