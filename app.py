# ✅ Flask backend using modular blueprints (ready for Render)
# Structure includes: auth, otp, payment, admin, student routes

from flask import Flask, send_from_directory, redirect
from flask_cors import CORS
import os

# Import route blueprints
from auth import auth_routes
from otp.email_otp import otp_routes
from payment import payment_routes
from admin import admin_routes
from student.student_routes import student_routes  # <-- new module to handle subject, upload, etc.

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)
app.secret_key = 'eKhGiWsVT0fqxEU98VWp'

# Register Blueprints
app.register_blueprint(auth_routes, url_prefix='/auth')
app.register_blueprint(otp_routes, url_prefix='/otp')
app.register_blueprint(payment_routes, url_prefix='/payment')
app.register_blueprint(admin_routes, url_prefix='/admin')
app.register_blueprint(student_routes, url_prefix='/student')

# Serve uploaded files (answers, questions, keys)
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

# ✅ Serve uploaded payment screenshots (e.g., user_payment.jpg)
@app.route('/uploads/<filename>')
def serve_uploads(filename):
    return send_from_directory('uploads', filename)

# Ensure folder structure exists
for subfolder in ['uploads', 'uploads/questions', 'uploads/answers', 'uploads/keys']:
    os.makedirs(subfolder, exist_ok=True)

@app.route('/')
def home():
    return redirect('/admin')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
