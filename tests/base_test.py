import unittest
from app import create_app
from config.database import db

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        # Pass config directly so app initializes WITH the URI already set
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'JWT_COOKIE_CSRF_PROTECT': False
        })
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()