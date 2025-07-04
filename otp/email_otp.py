from flask import Blueprint, request, jsonify
import smtplib
import random
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

from models import User
from db import db

load_dotenv()

otp_routes = Blueprint('otp', __name__)
email_otps = {}  # In-memory OTP storage, valid for 5 mins


@otp_routes.route('/send', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data.get('email')

    otp = str(random.randint(100000, 999999))
    email_otps[email] = {
        'otp': otp,
        'expires_at': datetime.utcnow() + timedelta(minutes=5)
    }

    sender = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")
    message = f"Subject: Your OTP\n\nYour OTP is {otp}. It is valid for 5 minutes."

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, email, message)
        return jsonify({'msg': 'OTP sent'}), 200
    except Exception as e:
        return jsonify({'msg': f'Failed to send OTP: {str(e)}'}), 500


@otp_routes.route('/verify', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp_input = data.get('otp')

    record = email_otps.get(email)
    if not record or datetime.utcnow() > record['expires_at']:
        return jsonify({'msg': 'OTP expired or not found'}), 400

    if record['otp'] != otp_input:
        return jsonify({'msg': 'Invalid OTP'}), 400

    user = User.query.filter_by(email=email).first()
    if user:
        user.is_verified = True
        db.session.commit()

    return jsonify({'msg': 'OTP verified'}), 200
