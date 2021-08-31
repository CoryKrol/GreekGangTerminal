import unittest

from app import create_app, db
from app.models import Role, Stock, User


class ModelStockTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_is_watched_by(self):
        # Assert user not watching stock
        user = User(email='student@utdallas.edu', password='password')
        stock = Stock(name='Apple', ticker='AAPL', sector="Tech", is_active=True, year_high=1000.0, year_low=100.0)
        db.session.add(user)
        db.session.add(stock)
        db.session.commit()
        self.assertFalse(user.is_watching(stock))
        self.assertFalse(stock.is_watched_by(user))

    def test_to_json(self):
        stock = Stock(name='Apple', ticker='AAPL', sector="Tech", is_active=True, year_high=1000.0, year_low=100.0)
        db.session.add(stock)
        db.session.commit()
        with self.app.test_request_context('/'):
            stock_json = stock.to_json()
        self.assertEqual(stock.name, stock_json['name'], 'Stock names not equal')
        self.assertEqual(stock.ticker, stock_json['ticker'], 'Stock tickers not equal')
        self.assertEqual(stock.sector, stock_json['sector'], 'Stock sectors not equal')
        self.assertEqual(stock.year_high, stock_json['year_high'], 'Stock 52-week high not equal')
        self.assertEqual(stock.year_low, stock_json['year_low'], 'Stock 52-week low not equal')
        self.assertTrue(stock_json['is_active'])
        self.assertEqual('/api/v1/stocks/' + stock.ticker, stock_json['url'])

    def test_from_json(self):
        stock1 = Stock(name='Apple', ticker='AAPL', sector="Tech", is_active=False, year_high=1000.0, year_low=100.0)
        db.session.add(stock1)
        db.session.commit()
        with self.app.test_request_context('/'):
            stock_json = stock1.to_json()
        stock2 = Stock.from_json(stock_json)
        self.assertEqual(stock1.name, stock2.name, 'Stock names not equal')
        self.assertEqual(stock1.ticker, stock2.ticker, 'Stock tickers not equal')
        self.assertEqual(stock1.sector, stock2.sector, 'Stock sectors not equal')
        self.assertEqual(stock1.year_high, stock2.year_high, 'Stock 52-week high not equal')
        self.assertEqual(stock1.year_low, stock2.year_low, 'Stock 52-week low not equal')
        self.assertFalse(stock2.is_active)
