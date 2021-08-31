import re
import unittest
from app import create_app, db
from app.models import User, Role
from typing import Final

STUDENT_EMAIL: Final = 'student@utdallas.edu'


class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(200, response.status_code)
        self.assertTrue(b'NPC' in response.data)

    def test_register_and_login(self):
        # Register new account
        response = self.client.post('/auth/register', data={
            'email': STUDENT_EMAIL,
            'username': 'student',
            'password': 'password',
            'password2': 'password'
        })
        self.assertEqual(302, response.status_code)

        # Login with new account
        response = self.client.post('/auth/login', data={
            'email': STUDENT_EMAIL,
            'password': 'password'
        }, follow_redirects=True)
        self.assertEqual(200, response.status_code)
        self.assertTrue(re.search(b'Hello,\\s+student!', response.data))
        self.assertTrue(b'You have not confirmed your account yet' in response.data)

        # Send confirmation token
        user = User.query.filter_by(email=STUDENT_EMAIL).first()
        token = user.generate_account_confirmation_token()
        response = self.client.get('/auth/confirmation/{}'.format(token), follow_redirects=True)
        user.confirm(token)
        self.assertEqual(200, response.status_code)
        self.assertTrue(b'Account created successfully.' in response.data)

        # Logout
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(200, response.status_code)
        self.assertTrue(b'You are now logged out.' in response.data)
