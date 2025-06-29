from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from dotenv import load_dotenv
import os

load_dotenv()

auth_routes = Blueprint('auth', __name__)
SECRET_KEY = os.getenv("SECRET_KEY")

# Simulated in-memory user DB (replace with actual DB)
from global_state import users

@auth_routes.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if email in users:
        return jsonify({'msg': 'User already exists'}), 400

    users[email] = {
        'password': generate_password_hash(password),
        'is_verified': False,
        'is_subscribed': False
    }
    return jsonify({'msg': 'Signup successful'}), 201

@auth_routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = users.get(email)
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'msg': 'Invalid credentials'}), 401

    token = jwt.encode(
        {'email': email, 'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)},
        SECRET_KEY, algorithm="HS256"
    )
    return jsonify({
        'token': token,
        'is_verified': user['is_verified'],
        'is_subscribed': user['is_subscribed']
    })
