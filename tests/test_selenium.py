import re
import threading
import time
import unittest
from selenium import webdriver
from app import create_app, db, fake
from app.models import Role, User, Stock


# noinspection PyPep8
class SeleniumTestCase(unittest.TestCase):
    client = None

    # noinspection PyPep8,PyBroadException
    @classmethod
    def setUpClass(cls):
        # Start Chrome
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        try:
            cls.client = webdriver.Chrome(options=options)
        except:
            pass

        # Skip tests if browser not started
        if cls.client:
            # Create application
            cls.app = create_app('testing')
            cls.app_context = cls.app.app_context()
            cls.app_context.push()

            import logging
            logger = logging.getLogger('werkzeug')
            logger.setLevel("ERROR")

            # Create database and populate with data
            db.create_all()
            Role.insert_roles()
            fake.users(10)
            stock = Stock(name='Apple', ticker='AAPL', sector="Tech", is_active=True, year_high=1000.0, year_low=100.0)
            db.session.add(stock)
            db.session.commit()
            fake.trades(10)

            # Add administrator user
            admin_role = Role.query.filter_by(name='Administrator').first()
            admin = User(email='student@utdallas.edu',
                         username='student',
                         password='password',
                         role=admin_role,
                         confirmed=True)
            db.session.add(admin)
            db.session.commit()

            # Start Flask server in a thread
            cls.server_thread = threading.Thread(target=cls.app.run, kwargs={'debug': False})
            cls.server_thread.start()

            time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        if cls.client:
            # Stop the flask server and the browser
            cls.client.get('http://localhost:5000/shutdown')
            cls.client.quit()
            cls.server_thread.join()

            # Destroy database
            db.drop_all()
            db.session.remove()

            # Remove application context
            cls.app_context.pop()

    def setUp(self):
        if not self.client:
            self.skipTest('Web browser not available')

    def tearDown(self):
        """Not needed"""
        pass

    def test_admin_home_page(self):
        # Navigate to home
        self.client.get('http://localhost:5000/')
        self.assertTrue(re.search('Hello,\\s+NPC\\s?!', self.client.page_source))

        # Navigate to login
        self.client.find_element_by_link_text('Log In').click()
        self.assertIn('<h1>Login</h1>', self.client.page_source)

        # Login
        self.client.find_element_by_name('email').send_keys('student@utdallas.edu')
        self.client.find_element_by_name('password').send_keys('password')
        self.client.find_element_by_name('submit').click()
        self.assertTrue(re.search('Hello,\\s+student!', self.client.page_source))

        # navigate to the user's profile page
        self.client.find_element_by_link_text('Account').click()
        self.client.find_element_by_link_text('Profile').click()
        self.assertIn('<h1>student</h1>', self.client.page_source)
