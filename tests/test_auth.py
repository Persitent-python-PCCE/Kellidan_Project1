from tests.base_test import BaseTestCase

class TestAuth(BaseTestCase):
    def test_api_registration_and_login(self):
        # Registration
        res = self.client.post('/api/register', json={
            "username": "api_student",
            "password": "password123",
            "role": "STUDENT"
        })
        self.assertEqual(res.status_code, 201)

        # Login
        res = self.client.post('/api/login', json={
            "username": "api_student",
            "password": "password123"
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn('access_token', res.get_json())

    def test_web_registration_and_login(self):
        # Registration
        res = self.client.post('/register', data={
            "username": "web_student",
            "password": "password123",
            "role": "STUDENT"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Registration successful', res.data)

        # Login
        res = self.client.post('/login', data={
            "username": "web_student",
            "password": "password123"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Logged in successfully', res.data)

    def test_unauthorized_access(self):
        res = self.client.get('/dashboard/admin')
        self.assertIn(res.status_code, [302, 401, 403])

    def test_web_logout(self):
        self.client.post('/register', data={
            "username": "logout_user",
            "password": "password123",
            "role": "STUDENT"
        }, follow_redirects=True)

        self.client.post('/login', data={
            "username": "logout_user",
            "password": "password123"
        }, follow_redirects=True)

        res = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Logged out successfully', res.data)
