import json
import unittest
from base64 import b64encode
from typing import Final

from app import create_app, db
from app.models import User, Role, Stock

CONTENT_TYPE: Final = 'application/json'
API_V1_TRADES: Final = '/api/v1/trades/'
API_V1_USERS_UNWATCH: Final = '/api/v1/users/{}/unwatch/{}'
API_V1_USERS_WATCHLIST: Final = '/api/v1/users/{}/watchlist/'
STUDENT_EMAIL: Final = 'student@utdallas.edu'
TA_EMAIL: Final = 'ta@utdallas.edu'
TA_PASSWORD: Final = 'pa$$w0rd'
LOCALHOST: Final = 'http://localhost'


class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @staticmethod
    def get_api_headers(username, password):
        return {
            'Authorization': 'Basic ' + b64encode((username + ':' + password).encode('utf-8')).decode('utf-8'),
            'Accept': CONTENT_TYPE,
            'Content-Type': CONTENT_TYPE
        }

    def test_404(self):
        response = self.client.get('/incorrect', headers=self.get_api_headers('email', 'password'))
        self.assertEqual(404, response.status_code)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual('not found', json_response['error'])

    def test_no_auth(self):
        response = self.client.get(API_V1_TRADES, content_type=CONTENT_TYPE)
        self.assertEqual(401, response.status_code)

    def test_bad_auth(self):
        # Add user
        role = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(role)
        user = User(email=STUDENT_EMAIL, password='password', confirmed=True, role=role)
        db.session.add(user)
        db.session.commit()

        # Authenticate with incorrect password
        response = self.client.get(API_V1_TRADES, headers=self.get_api_headers(STUDENT_EMAIL, TA_PASSWORD))
        self.assertEqual(401, response.status_code)

    def test_token_auth(self):
        # Add user
        role = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(role)
        user = User(email=STUDENT_EMAIL, password='password', confirmed=True, role=role)
        db.session.add(user)
        db.session.commit()

        # Issue request with incorrect token
        response = self.client.get(API_V1_TRADES, headers=self.get_api_headers('incorrect-token', ''))
        self.assertEqual(401, response.status_code)

        # Get token
        response = self.client.post('/api/v1/tokens/', headers=self.get_api_headers(STUDENT_EMAIL, 'password'))
        self.assertOkResponse(response)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('token'))
        token = json_response['token']

        # Issue request with token
        response = self.client.get(API_V1_TRADES, headers=self.get_api_headers(token, ''))
        self.assertOkResponse(response)

    def test_anonymous(self):
        response = self.client.get(API_V1_TRADES, headers=self.get_api_headers('', ''))
        self.assertEqual(401, response.status_code)

    def test_unconfirmed_account(self):
        # Add unconfirmed user
        role = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(role)
        user = User(email=STUDENT_EMAIL, password='password', confirmed=False, role=role)
        db.session.add(user)
        db.session.commit()

        # Get list of trades with unconfirmed account
        response = self.client.get(API_V1_TRADES, headers=self.get_api_headers(STUDENT_EMAIL, 'password'))
        self.assertEqual(403, response.status_code)

    def test_trades(self):
        # Add user
        role = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(role)
        user1 = User(username='student', email=STUDENT_EMAIL, password='password', confirmed=True, role=role)
        user2 = User(username='ta', email=TA_EMAIL, password=TA_PASSWORD, confirmed=True, role=role)
        stock1 = Stock(name='Apple', ticker='AAPL', sector="Tech", is_active=True, year_high=1000.0, year_low=100.0)
        stock2 = Stock(name='Nokia', ticker='NOK', sector="Tech", is_active=True, year_high=1000.0, year_low=100.0)
        db.session.add_all([user1, user2])
        user2.follow(user1)
        db.session.add_all([stock1, stock2, user1, user2])
        db.session.commit()

        # Create empty trade
        response = self.client.post(
            API_V1_TRADES,
            headers=self.get_api_headers(STUDENT_EMAIL, 'password'),
            data=json.dumps({'stock': '', 'user': '', 'quantity': '', 'price': ''}))
        self.assertEqual(400, response.status_code)

        # Create trade
        response = self.client.post(
            API_V1_TRADES,
            headers=self.get_api_headers(STUDENT_EMAIL, 'password'),
            data=json.dumps({'stock': stock1.ticker, 'user': user1.username, 'quantity': 1, 'price': 1.0}))
        self.assertEqual(201, response.status_code)
        url = response.headers.get('Location')
        self.assertIsNotNone(url)

        # Get new trade
        response = self.client.get(
            url,
            headers=self.get_api_headers(STUDENT_EMAIL, 'password'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(url, LOCALHOST + json_response['url'])
        self.assertEqual(stock1.ticker, json_response['stock'])
        self.assertEqual(user1.username, json_response['user'])
        self.assertEqual(1, json_response['quantity'])
        self.assertEqual(1.0, json_response['price'])
        json_trade = json_response

        # Get trade from the user
        response = self.client.get(
            '/api/v1/users/{}/trades/'.format(user1.username),
            headers=self.get_api_headers(STUDENT_EMAIL, 'password'))
        self.assertOkResponse(response)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('trades'))
        self.assertEqual(1, json_response.get('count', 0))
        self.assertEqual(json_trade, json_response['trades'][0])

        # Get the trade from the user as a follower
        response = self.client.get(
            '/api/v1/users/{}/timeline/'.format(user2.username),
            headers=self.get_api_headers(TA_EMAIL, TA_PASSWORD))
        self.assertOkResponse(response)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('trades'))
        self.assertEqual(1, json_response.get('count', 0))
        self.assertEqual(json_trade, json_response['trades'][0])

        # Edit trade
        response = self.client.put(
            url,
            headers=self.get_api_headers(STUDENT_EMAIL, 'password'),
            data=json.dumps({'stock': stock2.ticker, 'user': user1.username, 'quantity': 3, 'price': 3.0}))
        self.assertOkResponse(response)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(url, LOCALHOST + json_response['url'])
        self.assertEqual('NOK', json_response['stock'])
        self.assertEqual(3, json_response['quantity'])
        self.assertEqual(3.0, json_response['price'])

    def test_stocks(self):
        # Add user
        role = Role.query.filter_by(name='Administrator').first()
        self.assertIsNotNone(role)
        user = User(username='student', email=STUDENT_EMAIL, password='password', confirmed=True, role=role)
        db.session.add(user)
        db.session.commit()

        # New stock
        response = self.client.post(
            '/api/v1/stocks/',
            headers=self.get_api_headers(STUDENT_EMAIL, 'password'),
            data=json.dumps({'name': '', 'ticker': '', 'sector': '', 'year_high': '', 'year_low': ''}))
        self.assertEqual(400, response.status_code)

        # Create stock
        response = self.client.post(
            '/api/v1/stocks/',
            headers=self.get_api_headers(STUDENT_EMAIL, 'password'),
            data=json.dumps({
                'name': 'Apple',
                'ticker': 'AAPL',
                'sector': 'Tech',
                'year_high': 1000,
                'year_low': 100}))
        self.assertEqual(201, response.status_code)
        url = response.headers.get('Location')
        self.assertIsNotNone(url)

        # Get new stock
        response = self.client.get(
            url,
            headers=self.get_api_headers(STUDENT_EMAIL, 'password'))
        self.assertOkResponse(response)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(url, LOCALHOST + json_response['url'])
        self.assertEqual('Apple', json_response['name'])
        self.assertEqual('AAPL', json_response['ticker'])
        self.assertEqual('Tech', json_response['sector'])
        self.assertEqual(1000, json_response['year_high'])
        self.assertEqual(100, json_response['year_low'])
        json_stock = json_response

        # Have user watch stock
        stock = Stock.query.filter_by(ticker=json_stock['ticker']).first()
        self.assertFalse(user.is_watching(stock=stock))
        user.watch(stock=stock)
        self.assertTrue(user.is_watching(stock=stock))

        # Get stock from the user
        response = self.client.get(
            API_V1_USERS_WATCHLIST.format(user.username),
            headers=self.get_api_headers(STUDENT_EMAIL, 'password'))
        self.assertOkResponse(response)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('stocks'))
        self.assertEqual(1, json_response.get('count', 0))
        self.assertEqual(json_stock['ticker'], json_response['stocks'][0]['stock'])

        # Edit stock
        response = self.client.put(
            url,
            headers=self.get_api_headers(STUDENT_EMAIL, 'password'),
            data=json.dumps({
                'name': stock.name,
                'ticker': stock.ticker,
                'sector': stock.sector,
                'year_high': 500,
                'year_low': 100}))
        self.assertOkResponse(response)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(url, LOCALHOST + json_response['url'])
        self.assertEqual('Apple', json_response['name'])
        self.assertEqual('AAPL', json_response['ticker'])
        self.assertEqual('Tech', json_response['sector'])
        self.assertEqual(500, json_response['year_high'])
        self.assertEqual(100, json_response['year_low'])

    def test_users(self):
        # Add 2 users
        role = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(role)
        user1 = User(email=STUDENT_EMAIL, username='student', password='password', confirmed=True, role=role)
        user2 = User(email=TA_EMAIL, username='ta', password=TA_PASSWORD, confirmed=True, role=role)
        stock = Stock(name='Apple', ticker='AAPL', sector="Tech", is_active=True, year_high=1000.0, year_low=100.0)
        db.session.add_all([user1, user2, stock])
        db.session.commit()

        # Get users
        response = self.client.get(
            '/api/v1/users/{}'.format(user1.username),
            headers=self.get_api_headers(TA_EMAIL, TA_PASSWORD))
        self.assertOkResponse(response)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual('student', json_response['username'])
        response = self.client.get(
            '/api/v1/users/{}'.format(user2.username),
            headers=self.get_api_headers(TA_EMAIL, TA_PASSWORD))
        self.assertOkResponse(response)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual('ta', json_response['username'])

        # Have user2 attempt to add stock to another user's watchlist and get 403 error
        response = self.client.get('/api/v1/users/{}/watch/{}'.format(user1.username, stock.ticker),
                                   headers=self.get_api_headers(TA_EMAIL, TA_PASSWORD))
        self.assertEqual(403, response.status_code)

        # Have user watch stock
        self.assertFalse(user1.is_watching(stock=stock))
        response = self.client.get('/api/v1/users/{}/watch/{}'.format(user1.username, stock.ticker),
                                   headers=self.get_api_headers(STUDENT_EMAIL, 'password'))
        self.assertEqual(201, response.status_code)
        url = response.headers.get('Location')
        self.assertEqual(LOCALHOST + API_V1_USERS_UNWATCH.format(user1.username, stock.ticker), url)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(user1.username, json_response['user'])
        self.assertEqual(stock.ticker, json_response['stock'])
        self.assertTrue(user1.is_watching(stock=stock))

        # Have user 2 attempt to get user1's watchlist and receive 403 error
        response = self.client.get(API_V1_USERS_WATCHLIST.format(user1.username),
                                   headers=self.get_api_headers(TA_EMAIL, TA_PASSWORD))
        self.assertEqual(403, response.status_code)

        # Get user1's watchlist
        response = self.client.get(API_V1_USERS_WATCHLIST.format(user1.username),
                                   headers=self.get_api_headers(STUDENT_EMAIL, 'password'))
        self.assertOkResponse(response)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('stocks'))
        self.assertEqual(1, json_response.get('count', 0))

        # Have user2 attempt to remove stock from another user's watchlist and get 403 error
        response = self.client.get(API_V1_USERS_UNWATCH.format(user1.username, stock.ticker),
                                   headers=self.get_api_headers(TA_EMAIL, TA_PASSWORD))
        self.assertEqual(403, response.status_code)

        # Have user unwatch stock
        self.assertTrue(user1.is_watching(stock=stock))
        response = self.client.get(API_V1_USERS_UNWATCH.format(user1.username, stock.ticker),
                                   headers=self.get_api_headers(STUDENT_EMAIL, 'password'))
        self.assertEqual(204, response.status_code)

    # Helper functions
    def assertOkResponse(self, response):
        self.assertEqual(200, response.status_code)
