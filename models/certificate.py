import uuid
from datetime import datetime, timezone
from config.database import db

class Certificate(db.Model):
    __tablename__ = "certificates"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    certificate_code = db.Column(db.String(64), unique=True, nullable=False, default=lambda: uuid.uuid4().hex[:16].upper())
    issued_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref=db.backref('certificates', lazy=True, cascade="all, delete-orphan"))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'course_id', name='uq_user_course_certificate'),
    )
