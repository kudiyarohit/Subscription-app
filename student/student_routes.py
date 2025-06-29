from flask import Blueprint, request, jsonify, send_from_directory, current_app
from werkzeug.utils import secure_filename
import datetime, os

student_routes = Blueprint('student_routes', __name__)

# Simulated in-memory store (shared reference; ideally move to database)
from global_state import users, subjects  # shared memory reference

# 🧠 Helper Functions
def get_email_from_token(token):
    return token if token in users else None

def find_subject(sid):
    return next((s for s in subjects if str(s['id']) == str(sid)), None)

# 🎓 View Subjects with Question + Answer Key (if 1 hour passed)
@student_routes.route('/subjects', methods=['GET'])
def list_subjects():
    token = request.headers.get('Authorization')
    email = get_email_from_token(token)
    if not email:
        return 'Unauthorized', 401

    now = datetime.datetime.utcnow()
    result = []
    for s in subjects:
        a = s.get('answers', {}).get(email)
        uploaded_time = datetime.datetime.fromisoformat(a['time']) if a else None
        key_ready = uploaded_time and (now - uploaded_time).total_seconds() >= 3600

        result.append({
            'id': s['id'],
            'name': s['name'],
            'question_file': f"/files/questions/{s['question_file']}",
            'answer_uploaded': bool(a),
            'key_ready': key_ready,
            'answer_key': f"/files/keys/{s['keys']['file']}" if key_ready and 'keys' in s else None,
            'marks': s.get('marks', {}).get(email)
        })
    return jsonify(result)

# 📤 Upload student answer
@student_routes.route('/upload', methods=['POST'])
def upload_answer():
    token = request.headers.get('Authorization')
    email = get_email_from_token(token)
    if not email:
        return 'Unauthorized', 401

    sid = request.form.get('subject_id')
    pdf = request.files.get('answer_pdf')
    if not sid or not pdf:
        return 'Missing form data', 400

    subject = find_subject(sid)
    if not subject:
        return 'Invalid subject', 400

    filename = secure_filename(f"{email}_{sid}.pdf")
    filepath = os.path.join(current_app.config['ANSWERS_FOLDER'], filename)
    pdf.save(filepath)

    subject.setdefault('answers', {})[email] = {
        'file': filename,
        'time': datetime.datetime.utcnow().isoformat()
    }
    return 'Answer uploaded successfully', 200
