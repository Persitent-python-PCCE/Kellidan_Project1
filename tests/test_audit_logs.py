from tests.base_test import BaseTestCase
from dao.user_dao import UserDAO
from dao.audit_dao import AuditDAO

class TestAuditLogs(BaseTestCase):
    def test_audit_logs_recorded_and_viewable_by_admin(self):
        # 1. Register a student and login (generates audit logs)
        self.client.post('/register', data={
            'username': 'audit_test_student',
            'password': 'password123',
            'role': 'STUDENT'
        }, follow_redirects=True)

        self.client.post('/login', data={
            'username': 'audit_test_student',
            'password': 'password123'
        }, follow_redirects=True)

        # 2. Check that audit logs exist in DB
        with self.app.app_context():
            audit_dao = AuditDAO()
            logs = audit_dao.get_recent_logs(limit=20)
            action_names = [log.action for log in logs]
            self.assertIn('USER_REGISTER', action_names)
            self.assertIn('USER_LOGIN_SUCCESS', action_names)

        # 3. Create Admin & access audit log dashboard
        with self.app.app_context():
            u_dao = UserDAO()
            u_dao.create_user('audit_superadmin', 'adminpass', 'ADMIN')

        self.client.get('/logout', follow_redirects=True)
        self.client.post('/login', data={
            'username': 'audit_superadmin',
            'password': 'adminpass'
        }, follow_redirects=True)

        res = self.client.get('/dashboard/admin/audit-logs')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Security & Operations Audit Logs', res.data)
        self.assertIn(b'audit_test_student', res.data)
