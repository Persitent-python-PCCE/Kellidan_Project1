from tests.base_test import BaseTestCase
from config.database import db
from models.course import Course
from dao.user_dao import UserDAO
from dao.course_dao import CourseDAO

class TestReviews(BaseTestCase):
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            u_dao = UserDAO()
            c_dao = CourseDAO()
            inst = u_dao.create_user('inst_rev', 'pass', 'INSTRUCTOR')
            course = c_dao.create_course('FastAPI Full Course', 'Modern Python APIs', inst.id)
            self.course_id = course.id

        # Register and login student 1
        self.client.post('/register', data={
            'username': 'student_reviewer_1',
            'password': 'password123',
            'role': 'STUDENT'
        }, follow_redirects=True)

        self.client.post('/login', data={
            'username': 'student_reviewer_1',
            'password': 'password123'
        }, follow_redirects=True)

    def test_review_submission_and_average_rating(self):
        # 1. Student 1 submits a 5-star review
        res = self.client.post(f'/courses/{self.course_id}/reviews', data={
            'rating': '5',
            'comment': 'Outstanding course material and clarity!'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Thank you for your review!', res.data)
        self.assertIn(b'Outstanding course material', res.data)

        # Average rating is 5.0
        with self.app.app_context():
            c = db.session.get(Course, self.course_id)
            self.assertEqual(c.average_rating, 5.0)

        # 2. Student 2 registers, logs in, and submits a 3-star review
        self.client.get('/logout', follow_redirects=True)
        self.client.post('/register', data={
            'username': 'student_reviewer_2',
            'password': 'password123',
            'role': 'STUDENT'
        }, follow_redirects=True)
        self.client.post('/login', data={
            'username': 'student_reviewer_2',
            'password': 'password123'
        }, follow_redirects=True)

        self.client.post(f'/courses/{self.course_id}/reviews', data={
            'rating': '3',
            'comment': 'Good, but could use more exercises.'
        }, follow_redirects=True)

        # Average rating is now (5 + 3) / 2 = 4.0
        with self.app.app_context():
            c = db.session.get(Course, self.course_id)
            self.assertEqual(c.average_rating, 4.0)

    def test_invalid_review_rating(self):
        res = self.client.post(f'/courses/{self.course_id}/reviews', data={
            'rating': '10', # Invalid rating
            'comment': 'Over the top'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Please select a valid rating', res.data)
