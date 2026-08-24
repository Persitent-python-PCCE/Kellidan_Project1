from tests.base_test import BaseTestCase
from dao.user_dao import UserDAO
from dao.course_dao import CourseDAO
from dao.quiz_dao import QuizDAO

class TestStudent(BaseTestCase):
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            u_dao = UserDAO()
            c_dao = CourseDAO()
            q_dao = QuizDAO()
            inst = u_dao.create_user('prof_doe', 'pass', 'INSTRUCTOR')
            course = c_dao.create_course('Web Fundamentals', 'HTML, CSS, JS', inst.id)
            self.course_id = course.id
            quiz = q_dao.create_quiz(self.course_id, 'HTML Basics Quiz')
            self.quiz_id = quiz.id
            q = q_dao.add_question(self.quiz_id, 'What does HTML stand for?', 'HyperText Markup Language', 'Home Tool', 'HyperLinks', 'None', 'A')
            self.question_id = q.id

        # Register and login student
        self.client.post('/register', data={
            'username': 'alice_student',
            'password': 'password123',
            'role': 'STUDENT'
        }, follow_redirects=True)

        self.client.post('/login', data={
            'username': 'alice_student',
            'password': 'password123'
        }, follow_redirects=True)

    def test_student_dashboard_and_catalog(self):
        res = self.client.get('/dashboard/student')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Student Dashboard', res.data)
        self.assertIn(b'alice_student', res.data)

        res = self.client.get('/courses')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Web Fundamentals', res.data)

    def test_enrollment_flow(self):
        # Enroll in course
        res = self.client.post(f'/courses/enroll/{self.course_id}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Enrolled successfully!', res.data)

        # Student dashboard now displays the enrolled course
        res = self.client.get('/dashboard/student')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Web Fundamentals', res.data)

    def test_quiz_attempt_and_progress_history(self):
        # Attempt Quiz with correct answer
        res = self.client.post(f'/quiz/{self.quiz_id}', data={str(self.question_id): 'A'}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Quiz completed! You scored 100.00%', res.data)

        # Progress history page shows 100% score
        res = self.client.get('/progress')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'100', res.data)
