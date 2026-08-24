from config.database import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="STUDENT") # ADMIN, INSTRUCTOR, STUDENT

    enrollments = db.relationship('Enrollment', backref='student', cascade="all, delete-orphan")
    quiz_results = db.relationship('QuizResult', backref='student', cascade="all, delete-orphan")
    lesson_progress = db.relationship('LessonProgress', backref='user', cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {"id": self.id, "username": self.username, "role": self.role}