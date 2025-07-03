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
                        username = users.get(email, {}).get("username", email)  # ✅ show name
                        answers_by_subject[sid].append({
                            'email': username,
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

# ✅ Delete subject route
@admin_routes.route('/delete_subject', methods=['POST'])
def delete_subject():
    sid = request.form.get('subject_id')

    subject = next((s for s in subjects if str(s['id']) == str(sid)), None)
    if not subject:
        return 'Invalid subject', 400

    # Delete question file
    qfile = subject.get('question_file')
    if qfile:
        qpath = os.path.join('uploads', 'questions', qfile)
        if os.path.exists(qpath):
            os.remove(qpath)

    # Delete answer key
    keyfile = subject.get('keys', {}).get('file')
    if keyfile:
        kpath = os.path.join('uploads', 'keys', keyfile)
        if os.path.exists(kpath):
            os.remove(kpath)

    # Delete all student answer files
    for email, info in subject.get('answers', {}).items():
        ans_path = os.path.join('uploads', 'answers', info['file'])
        if os.path.exists(ans_path):
            os.remove(ans_path)

    # Remove subject from list
    subjects.remove(subject)
    save_subjects()

    return redirect('/admin')


@admin_routes.route('/delete_subject_files', methods=['POST'])
def delete_subject_files():
    sid = request.form.get('subject_id')
    subject = next((s for s in subjects if str(s['id']) == str(sid)), None)

    if not subject:
        return 'Invalid subject', 400

    # Delete question file
    qfile_path = os.path.join("uploads", "questions", subject['question_file'])
    if os.path.exists(qfile_path):
        os.remove(qfile_path)

    # Delete answer key file (if exists)
    key_file = subject.get("keys", {}).get("file")
    if key_file:
        kfile_path = os.path.join("uploads", "keys", key_file)
        if os.path.exists(kfile_path):
            os.remove(kfile_path)
        subject['keys'] = {}

    # Remove from subject object
    subject['question_file'] = ""
    save_subjects()

    return redirect('/admin')