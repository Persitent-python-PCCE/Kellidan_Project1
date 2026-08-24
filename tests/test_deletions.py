from tests.base_test import BaseTestCase
from dao.user_dao import UserDAO
from dao.course_dao import CourseDAO
from dao.quiz_dao import QuizDAO

class TestDeleteOperations(BaseTestCase):
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            u_dao = UserDAO()
            c_dao = CourseDAO()
            q_dao = QuizDAO()

            self.admin = u_dao.create_user('super_admin', 'pass123', 'ADMIN')
            self.instructor = u_dao.create_user('inst_delete', 'pass123', 'INSTRUCTOR')
            self.student = u_dao.create_user('stu_delete', 'pass123', 'STUDENT')

            course = c_dao.create_course('Delete Target Course', 'To be deleted', self.instructor.id)
            self.course_id = course.id

            mod = c_dao.add_module(self.course_id, 'Module To Delete')
            self.module_id = mod.id
            c_dao.add_lesson(mod.id, 'Lesson 1', 'Content 1')

            quiz = q_dao.create_quiz(self.course_id, 'Quiz To Delete')
            self.quiz_id = quiz.id

            self.admin_id = self.admin.id
            self.instructor_id = self.instructor.id
            self.student_id = self.student.id

    def test_delete_module_and_quiz_by_instructor(self):
        # Login as instructor
        self.client.post('/login', data={'username': 'inst_delete', 'password': 'pass123'}, follow_redirects=True)

        # Delete Quiz
        res = self.client.post(f'/courses/{self.course_id}/quizzes/{self.quiz_id}/delete', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Quiz deleted successfully!', res.data)

        # Delete Module
        res = self.client.post(f'/courses/{self.course_id}/modules/{self.module_id}/delete', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Module deleted successfully!', res.data)

        with self.app.app_context():
            c_dao = CourseDAO()
            q_dao = QuizDAO()
            course = c_dao.get_course_by_id(self.course_id)
            self.assertEqual(len(course.modules), 0)
            self.assertEqual(len(course.quizzes), 0)

    def test_delete_course_by_instructor(self):
        self.client.post('/login', data={'username': 'inst_delete', 'password': 'pass123'}, follow_redirects=True)

        res = self.client.post(f'/courses/{self.course_id}/delete', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Course deleted successfully!', res.data)

        with self.app.app_context():
            c_dao = CourseDAO()
            self.assertIsNone(c_dao.get_course_by_id(self.course_id))

    def test_admin_delete_user(self):
        self.client.post('/login', data={'username': 'super_admin', 'password': 'pass123'}, follow_redirects=True)

        # Cannot delete self
        res = self.client.post(f'/dashboard/admin/users/{self.admin_id}/delete', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'cannot delete your own admin account', res.data)

        # Delete student user
        res = self.client.post(f'/dashboard/admin/users/{self.student_id}/delete', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'deleted successfully!', res.data)

        with self.app.app_context():
            u_dao = UserDAO()
            self.assertIsNone(u_dao.get_by_id(self.student_id))
