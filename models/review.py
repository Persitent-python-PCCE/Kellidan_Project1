from datetime import datetime, timezone
from config.database import db

class CourseReview(db.Model):
    __tablename__ = "course_reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1 to 5
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref=db.backref('reviews', lazy=True, cascade="all, delete-orphan"))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'course_id', name='uq_user_course_review'),
    )
