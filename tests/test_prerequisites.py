from tests.base_test import BaseTestCase
from dao.user_dao import UserDAO
from dao.course_dao import CourseDAO

class TestPrerequisites(BaseTestCase):
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            u_dao = UserDAO()
            c_dao = CourseDAO()
            inst = u_dao.create_user('inst_dept', 'pass', 'INSTRUCTOR')

            # 1. Course Level 1 (Intro)
            course_l1 = c_dao.create_course('Python 1: Intro', 'Basic Python', inst.id)
            mod_1 = c_dao.add_module(course_l1.id, 'Basics')
            lesson_1 = c_dao.add_lesson(mod_1.id, 'Lesson 1', 'Syntax')
            self.c1_id = course_l1.id
            self.l1_id = lesson_1.id

            # 2. Course Level 2 (Intermediate) requiring Course Level 1
            course_l2 = c_dao.create_course('Python 2: Intermediate', 'OOP and Patterns', inst.id, prerequisite_ids=[self.c1_id])
            self.c2_id = course_l2.id

        # Register and login student
        self.client.post('/register', data={
            'username': 'student_prereq_test',
            'password': 'password123',
            'role': 'STUDENT'
        }, follow_redirects=True)

        self.client.post('/login', data={
            'username': 'student_prereq_test',
            'password': 'password123'
        }, follow_redirects=True)

    def test_prerequisite_blocking_and_unlocking(self):
        # 1. Directly trying to enroll in Level 2 should fail
        res = self.client.post(f'/courses/enroll/{self.c2_id}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Prerequisites not met', res.data)
        self.assertIn(b'Python 1: Intro', res.data)

        # 2. Enroll in Level 1 and complete it (100%)
        self.client.post(f'/courses/enroll/{self.c1_id}', follow_redirects=True)
        self.client.post(f'/courses/{self.c1_id}/lessons/{self.l1_id}/toggle', follow_redirects=True)

        # 3. Now enrolling in Level 2 should succeed
        res = self.client.post(f'/courses/enroll/{self.c2_id}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Enrolled successfully!', res.data)
