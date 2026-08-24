from tests.base_test import BaseTestCase

class TestInstructor(BaseTestCase):
    def setUp(self):
        super().setUp()
        # Register and login instructor
        self.client.post('/register', data={
            'username': 'prof_smith',
            'password': 'password123',
            'role': 'INSTRUCTOR'
        }, follow_redirects=True)

        self.client.post('/login', data={
            'username': 'prof_smith',
            'password': 'password123'
        }, follow_redirects=True)

    def test_instructor_dashboard_view(self):
        res = self.client.get('/dashboard/instructor')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Instructor Dashboard', res.data)
        self.assertIn(b'prof_smith', res.data)

    def test_create_course(self):
        res = self.client.post('/courses/create', data={
            'title': 'Machine Learning Fundamentals',
            'description': 'An applied introduction to ML models.'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Machine Learning Fundamentals', res.data)

    def test_create_module_and_lesson(self):
        # Create course first
        self.client.post('/courses/create', data={
            'title': 'Deep Learning',
            'description': 'Neural Networks'
        }, follow_redirects=True)

        # Add Module
        res = self.client.post('/courses/1/modules', data={
            'title': 'Module 1: Perceptrons'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Module 1: Perceptrons', res.data)

        # Add Lesson to Module 1
        res = self.client.post('/courses/1/modules/1/lessons', data={
            'title': 'Lesson 1.1: Single Layer Perceptron',
            'content': 'Weights, biases, and activation functions.'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Single Layer Perceptron', res.data)

    def test_create_quiz(self):
        self.client.post('/courses/create', data={
            'title': 'Statistics 101',
            'description': 'Probability & Stats'
        }, follow_redirects=True)

        res = self.client.post('/courses/1/quizzes/create', data={
            'title': 'Probability Quiz 1',
            'question_text': 'What is the probability of flipping heads on a fair coin?',
            'option_a': '0.25',
            'option_b': '0.50',
            'option_c': '0.75',
            'option_d': '1.00',
            'correct_option': 'B'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Probability Quiz 1', res.data)
