from flask import Blueprint, request, jsonify
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

question_routes = Blueprint('questions', __name__)

SECRET_KEY = os.getenv("SECRET_KEY")

from global_state import users

subjects = [
    {"id": 1, "name": "Physics", "file": "https://example.com/physics.pdf"},
    {"id": 2, "name": "Maths", "file": "https://example.com/maths.pdf"},
    {"id": 3, "name": "Biology", "file": "https://example.com/biology.pdf"},
]

@question_routes.route('/subjects', methods=['GET'])
def get_subjects():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'msg': 'Missing token'}), 401

    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = decoded['email']
        if not users[email]['is_subscribed']:
            return jsonify({'msg': 'Not subscribed'}), 403
        return jsonify(subjects)
    except Exception:
        return jsonify({'msg': 'Invalid token'}), 403
