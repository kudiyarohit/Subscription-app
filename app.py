from flask import Flask, send_from_directory, redirect
from flask_cors import CORS
import os

# Initialize app
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)
from flask import Flask, send_from_directory, redirect
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize app
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# 🔐 Load secret from .env
app.secret_key = os.getenv("SECRET_KEY", "fallback-key")
app.config["JWT_SECRET_KEY"] = app.secret_key
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["JWT_HEADER_NAME"] = "Authorization"
app.config["JWT_HEADER_TYPE"] = ""  # if you're sending raw token without Bearer

# Initialize JWT
jwt = JWTManager(app)


# ------------------ DB Config ------------------ #
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Setup DB
from db import db
db.init_app(app)

# Create tables
with app.app_context():
    from models import *  # Import all models
    db.create_all()

# ------------------ Register Blueprints ------------------ #
from auth import auth_routes
from otp.email_otp import otp_routes
from payment import payment_routes
from admin import admin_routes
from student.student_routes import student_routes

app.register_blueprint(auth_routes, url_prefix='/auth')
app.register_blueprint(otp_routes, url_prefix='/otp')
app.register_blueprint(payment_routes, url_prefix='/payment')
app.register_blueprint(admin_routes, url_prefix='/admin')
app.register_blueprint(student_routes, url_prefix='/student')

# ------------------ Serve Uploaded Files ------------------ #
@app.route('/files/<folder>/<filename>')
def serve_file(folder, filename):
    dirs = {
        'questions': os.path.join('uploads', 'questions'),
        'answers': os.path.join('uploads', 'answers'),
        'keys': os.path.join('uploads', 'keys')
    }
    if folder in dirs:
        return send_from_directory(dirs[folder], filename)
    return 'Invalid folder', 404

@app.route('/uploads/<filename>')
def serve_uploads(filename):
    return send_from_directory('uploads', filename)

# ------------------ Ensure Folder Structure ------------------ #
for subfolder in ['uploads', 'uploads/questions', 'uploads/answers', 'uploads/keys']:
    os.makedirs(subfolder, exist_ok=True)

# ------------------ Default Route ------------------ #
@app.route('/')
def home():
    return redirect('/admin')

from flask import send_from_directory

@app.route('/uploads/answers/<path:filename>')
def serve_answer_pdf(filename):
    return send_from_directory('uploads/answers', filename)

# ------------------ Run App ------------------ #
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
