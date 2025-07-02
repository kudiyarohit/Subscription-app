import json
import os

# Base URL for serving files
BASE_URL = "https://improvement-test-medal-elements.trycloudflare.com/"

# File to persist users
USERS_FILE = 'users.json'

# Load users from disk (if exists)
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
else:
    users = {}

# Save users to disk
def save_users():
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

# Subjects file
SUBJECTS_FILE = 'subjects.json'

# Load subjects from disk (if exists)
if os.path.exists(SUBJECTS_FILE):
    with open(SUBJECTS_FILE, 'r') as f:
        subjects = json.load(f)
else:
    subjects = [
        {
            "id": 1,
            "name": "Accounts",
            "question_file": "Accounts.pdf",
            "keys": {"file": "Accounts_key.pdf"},
            "answers": {},
            "marks": {}
        }
    ]

# Save subjects to disk
def save_subjects():
    with open(SUBJECTS_FILE, 'w') as f:
        json.dump(subjects, f)

# Helper: get subject list with full URLs for API
def get_subjects_for_user(email):
    enriched = []
    for sub in subjects:
        s = sub.copy()

        # Add full file URL for question
        s['question_file'] = f"{BASE_URL}/files/questions/{sub['question_file']}"

        # Add key file if uploaded
        key_file = sub.get("keys", {}).get("file")
        s['answer_key'] = f"{BASE_URL}/files/keys/{key_file}" if key_file else None

        # Answer uploaded status
        s['answer_uploaded'] = email in sub.get("answers", {})

        # Key ready status (after submission)
        s['key_ready'] = email in sub.get("answers", {})

        # Marks (if evaluated)
        s['marks'] = sub.get("marks", {}).get(email)

        enriched.append(s)
    return enriched
