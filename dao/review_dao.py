from config.database import db
from models.review import CourseReview
from datetime import datetime, timezone

class ReviewDAO:
    def add_or_update_review(self, user_id, course_id, rating, comment=None):
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be an integer between 1 and 5")
        
        review = CourseReview.query.filter_by(user_id=user_id, course_id=course_id).first()
        if not review:
            review = CourseReview(user_id=user_id, course_id=course_id, rating=rating, comment=comment)
            db.session.add(review)
        else:
            review.rating = rating
            review.comment = comment
            review.created_at = datetime.now(timezone.utc)
        db.session.commit()
        return review

    def get_reviews_for_course(self, course_id):
        return CourseReview.query.filter_by(course_id=course_id).order_by(CourseReview.created_at.desc()).all()

    def get_user_review(self, user_id, course_id):
        return CourseReview.query.filter_by(user_id=user_id, course_id=course_id).first()
