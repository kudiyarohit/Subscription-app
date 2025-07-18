### ✅ models.py
from db import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    email = db.Column(db.String, primary_key=True)
    password = db.Column(db.String)
    username = db.Column(db.String)
    is_verified = db.Column(db.Boolean, default=False)
    is_subscribed = db.Column(db.Boolean, default=False)

    paid_subjects = db.relationship('Payment', backref='user', lazy=True)
    answers = db.relationship('Answer', backref='user', lazy=True)
    marks = db.relationship('Mark', backref='user', lazy=True)

class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    tests = db.relationship('Test', backref='subject', lazy=True)

class Test(db.Model):
    __tablename__ = 'tests'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    question_file = db.Column(db.String)
    key_file = db.Column(db.String, nullable=True)
    total_marks = db.Column(db.Integer)  # ✅ Total marks for this test

    answers = db.relationship('Answer', backref='test', lazy=True)
    marks = db.relationship('Mark', backref='test', lazy=True)

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String, db.ForeignKey('users.email'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    approved = db.Column(db.Boolean, default=False)
    screenshot_filename = db.Column(db.String)

class Answer(db.Model):
    __tablename__ = 'answers'
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String, db.ForeignKey('users.email'))
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'))
    file_name = db.Column(db.String)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

class Mark(db.Model):
    __tablename__ = 'marks'
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'))
    user_email = db.Column(db.String, db.ForeignKey('users.email'))
    score = db.Column(db.Float)  # Support decimal scores

class Otp(db.Model):
    __tablename__ = 'otps'
    email = db.Column(db.String, primary_key=True)
    otp = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)