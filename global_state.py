import json
import os

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

# Subjects (can also be stored in a DB in production)
subjects = [
    {
        "id": 1,
        "name": "Physics",
        "question_file": "physics.pdf",
        "keys": {"file": "physics_key.pdf"},
        "answers": {},     # email -> { file, time }
        "marks": {}        # email -> marks
    },
    {
        "id": 2,
        "name": "Maths",
        "question_file": "maths.pdf",
        "keys": {"file": "maths_key.pdf"},
        "answers": {},
        "marks": {}
    },
    {
        "id": 3,
        "name": "Biology",
        "question_file": "biology.pdf",
        "keys": {"file": "biology_key.pdf"},
        "answers": {},
        "marks": {}
    }
]
SUBJECTS_FILE = 'subjects.json'

def save_subjects():
    with open(SUBJECTS_FILE, 'w') as f:
        json.dump(subjects, f)

# Load from disk if available
if os.path.exists(SUBJECTS_FILE):
    with open(SUBJECTS_FILE, 'r') as f:
        subjects = json.load(f)