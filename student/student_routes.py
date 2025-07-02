from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import datetime, os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
student_routes = Blueprint('student_routes', __name__)

from global_state import users, subjects, save_subjects, get_subjects_for_user

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
    if not email or email not in users or not users[email]['is_subscribed']:
        return jsonify({"error": "Unauthorized or not subscribed"}), 401

    return jsonify(get_subjects_for_user(email))

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

    subject = find_subject(subject_id)
    if not subject:
        return jsonify({"error": "Invalid subject"}), 400

    # Save PDF
    ANSWERS_FOLDER = os.path.join('uploads', 'answers')
    os.makedirs(ANSWERS_FOLDER, exist_ok=True)

    filename = secure_filename(f"{email}_{subject_id}.pdf")
    filepath = os.path.join(ANSWERS_FOLDER, filename)
    pdf.save(filepath)

    subject.setdefault('answers', {})[email] = {
        'file': filename,
        'time': datetime.datetime.utcnow().isoformat()
    }

    save_subjects()
    return jsonify({"message": "Answer uploaded successfully"}), 200
