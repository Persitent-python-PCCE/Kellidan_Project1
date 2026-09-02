import os
import unittest
# Set env var BEFORE importing or running create_app
os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

from app import create_app
from config.database import db

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['JWT_COOKIE_CSRF_PROTECT'] = False
        self.client = self.app.test_client()

        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()