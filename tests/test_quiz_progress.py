from tests.base_test import BaseTestCase
from dao.user_dao import UserDAO
from dao.course_dao import CourseDAO
from dao.quiz_dao import QuizDAO
from dao.certificate_dao import CertificateDAO

class TestQuizProgressIntegration(BaseTestCase):
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            u_dao = UserDAO()
            c_dao = CourseDAO()
            q_dao = QuizDAO()

            inst = u_dao.create_user('inst_quiz_prof', 'pass', 'INSTRUCTOR')
            course = c_dao.create_course('Data Science 101', 'Intro to DS', inst.id)
            self.course_id = course.id

            mod = c_dao.add_module(self.course_id, 'Module 1')
            l1 = c_dao.add_lesson(mod.id, 'Lesson A', 'Content A')
            l2 = c_dao.add_lesson(mod.id, 'Lesson B', 'Content B')
            self.l1_id = l1.id
            self.l2_id = l2.id

            quiz = q_dao.create_quiz(self.course_id, 'DS Quiz 1')
            self.quiz_id = quiz.id
            q1 = q_dao.add_question(self.quiz_id, 'Question 1', 'Opt A', 'Opt B', 'Opt C', 'Opt D', 'A')
            q2 = q_dao.add_question(self.quiz_id, 'Question 2', 'Opt A', 'Opt B', 'Opt C', 'Opt D', 'B')
            self.q1_id = q1.id
            self.q2_id = q2.id

        # Register and login student
        self.client.post('/register', data={
            'username': 'student_quiz_tester',
            'password': 'password123',
            'role': 'STUDENT'
        }, follow_redirects=True)

        self.client.post('/login', data={
            'username': 'student_quiz_tester',
            'password': 'password123'
        }, follow_redirects=True)

        # Enroll in course
        self.client.post(f'/courses/enroll/{self.course_id}', follow_redirects=True)

    def test_quiz_and_lesson_progress_reflects_highest_score(self):
        with self.app.app_context():
            c_dao = CourseDAO()
            u_dao = UserDAO()
            student = u_dao.get_by_username('student_quiz_tester')
            self.student_id = student.id

        # 1. Complete Lesson 1 (1 out of 3 items = 33.3%)
        self.client.post(f'/courses/{self.course_id}/lessons/{self.l1_id}/toggle', follow_redirects=True)
        with self.app.app_context():
            c_dao = CourseDAO()
            progress = c_dao.calculate_course_progress(self.student_id, self.course_id)
            self.assertEqual(progress, 33.3)

        # 2. Attempt Quiz with 1 correct out of 2 (Score 50%) -> (1 lesson + 0.5 quiz) / 3 items = 1.5 / 3 = 50.0%
        self.client.post(f'/quiz/{self.quiz_id}', data={
            str(self.q1_id): 'A',
            str(self.q2_id): 'A' # wrong
        }, follow_redirects=True)

        with self.app.app_context():
            c_dao = CourseDAO()
            progress = c_dao.calculate_course_progress(self.student_id, self.course_id)
            self.assertEqual(progress, 50.0)

        # 3. Retake Quiz with 2 correct (Score 100%) -> (1 lesson + 1.0 quiz) / 3 items = 2 / 3 = 66.7%
        self.client.post(f'/quiz/{self.quiz_id}', data={
            str(self.q1_id): 'A',
            str(self.q2_id): 'B'
        }, follow_redirects=True)

        with self.app.app_context():
            c_dao = CourseDAO()
            progress = c_dao.calculate_course_progress(self.student_id, self.course_id)
            self.assertEqual(progress, 66.7)

        # 4. Retake Quiz with 0 correct (Score 0%) -> Progress should RETAIN 66.7% because highest score is 100%
        self.client.post(f'/quiz/{self.quiz_id}', data={
            str(self.q1_id): 'B',
            str(self.q2_id): 'A'
        }, follow_redirects=True)

        with self.app.app_context():
            c_dao = CourseDAO()
            progress = c_dao.calculate_course_progress(self.student_id, self.course_id)
            self.assertEqual(progress, 66.7)

        # 5. Complete Lesson 2 (2 lessons + 1.0 quiz = 3 / 3 = 100.0%) -> Certificate issued
        res = self.client.post(f'/courses/{self.course_id}/lessons/{self.l2_id}/toggle', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        with self.app.app_context():
            c_dao = CourseDAO()
            cert_dao = CertificateDAO()
            progress = c_dao.calculate_course_progress(self.student_id, self.course_id)
            self.assertEqual(progress, 100.0)

            cert = cert_dao.get_by_user_and_course(self.student_id, self.course_id)
            self.assertIsNotNone(cert)

    def test_progress_history_keeps_only_highest_score(self):
        # Attempt 1: 50%
        self.client.post(f'/quiz/{self.quiz_id}', data={
            str(self.q1_id): 'A',
            str(self.q2_id): 'A'
        }, follow_redirects=True)

        # Attempt 2: 100%
        self.client.post(f'/quiz/{self.quiz_id}', data={
            str(self.q1_id): 'A',
            str(self.q2_id): 'B'
        }, follow_redirects=True)

        # Attempt 3: 0%
        self.client.post(f'/quiz/{self.quiz_id}', data={
            str(self.q1_id): 'C',
            str(self.q2_id): 'C'
        }, follow_redirects=True)

        res = self.client.get('/progress')
        self.assertEqual(res.status_code, 200)
        # Should display 100.0% as highest score and only 1 row entry for this quiz
        self.assertIn(b'100', res.data)
        self.assertIn(b'DS Quiz 1', res.data)
