from flask import Blueprint, request, render_template_string, redirect
import os

admin_routes = Blueprint('admin', __name__)
UPLOAD_FOLDER = "uploads"


if not os.path.exists('uploads'):
    os.makedirs('uploads')

from global_state import users, subjects

@admin_routes.route('/')
def admin_dashboard():
    pending = []
    for filename in os.listdir(UPLOAD_FOLDER):
        email = filename.replace('_payment.jpg', '')
        if email in users and not users[email]['is_subscribed']:
            pending.append((email, f"/uploads/{filename}"))

    return render_template_string("""
        <h2>Pending Payments</h2>
        {% for email, img in pending %}
            <div>
                <p><strong>{{ email }}</strong></p>
                <img src="{{ img }}" height="200" />
                <form method="POST" action="/admin/approve">
                    <input type="hidden" name="email" value="{{ email }}" />
                    <button type="submit">Approve</button>
                </form>
            </div><hr>
        {% endfor %}
    """, pending=pending)

@admin_routes.route('/approve', methods=['POST'])
def approve_user():
    email = request.form.get('email')
    if email in users:
        users[email]['is_subscribed'] = True
    return redirect('/admin')
