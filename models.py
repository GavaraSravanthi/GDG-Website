from flask_login import UserMixin
from datetime import datetime

print("models.py loaded")  # ✅ Best placed after imports

class User(UserMixin):
    def __init__(self, user_id, email, password_hash,is_admin=False):
        self.id = str(user_id)
        self.email = email
        self.password_hash = password_hash
        self.is_admin = is_admin
def get_id(self):
        return self.id
class Event:
    def __init__(self, title, date, location, description, email):
        self.title = title
        self.date = date
        self.location = location
        self.description = description
        self.email = email
        self.created_at = datetime.utcnow()

    def to_dict(self):
        return {
            "title": self.title,
            "date": self.date,
            "location": self.location,
            "description": self.description,
            "email": self.email,
            "created_at": self.created_at
        }