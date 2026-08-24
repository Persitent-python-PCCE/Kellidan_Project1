from tests.base_test import BaseTestCase
from dao.user_dao import UserDAO
from dao.course_dao import CourseDAO
from dao.certificate_dao import CertificateDAO

class TestProgressAndCertificates(BaseTestCase):
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            u_dao = UserDAO()
            c_dao = CourseDAO()
            inst = u_dao.create_user('inst_progress', 'pass', 'INSTRUCTOR')
            course = c_dao.create_course('Python Mastery', 'Master Python from Scratch', inst.id)
            self.course_id = course.id

            mod = c_dao.add_module(self.course_id, 'Module 1: Syntax')
            l1 = c_dao.add_lesson(mod.id, 'Variables & Types', 'Intro notes')
            l2 = c_dao.add_lesson(mod.id, 'Functions & Loops', 'Control structures')
            self.l1_id = l1.id
            self.l2_id = l2.id

        # Register and login student
        self.client.post('/register', data={
            'username': 'bob_progress',
            'password': 'password123',
            'role': 'STUDENT'
        }, follow_redirects=True)

        self.client.post('/login', data={
            'username': 'bob_progress',
            'password': 'password123'
        }, follow_redirects=True)

        # Enroll in course
        self.client.post(f'/courses/enroll/{self.course_id}', follow_redirects=True)

    def test_granular_lesson_progress_tracking(self):
        # 1. Complete Lesson 1 -> 50%
        res = self.client.post(f'/courses/{self.course_id}/lessons/{self.l1_id}/toggle', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'50.0%', res.data)

        # 2. Toggle Lesson 1 back to incomplete -> 0%
        res = self.client.post(f'/courses/{self.course_id}/lessons/{self.l1_id}/toggle', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'0.0%', res.data)

    def test_100_percent_completion_and_certificate_generation(self):
        # Complete Lesson 1
        self.client.post(f'/courses/{self.course_id}/lessons/{self.l1_id}/toggle', follow_redirects=True)

        # Complete Lesson 2 -> triggers 100% and certificate
        res = self.client.post(f'/courses/{self.course_id}/lessons/{self.l2_id}/toggle', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Certificate of Completion Earned', res.data)

        # Verify Certificate in DB & retrieve code
        with self.app.app_context():
            cert_dao = CertificateDAO()
            user_dao = UserDAO()
            stu = user_dao.get_by_username('bob_progress')
            cert = cert_dao.get_by_user_and_course(stu.id, self.course_id)
            self.assertIsNotNone(cert)
            cert_id = cert.id
            cert_code = cert.certificate_code

        # View Printable Certificate
        res = self.client.get(f'/certificates/view/{cert_id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Certificate of Completion', res.data)
        self.assertIn(b'bob_progress', res.data)
        self.assertIn(b'Python Mastery', res.data)

        # Public Online Verification
        res = self.client.get(f'/certificates/verify/{cert_code}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Official Credential Verified', res.data)

        # Invalid certificate verification check
        res = self.client.get('/certificates/verify/INVALID-CODE-999')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Certificate Not Found', res.data)
