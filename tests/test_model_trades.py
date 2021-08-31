import unittest

from app import create_app, db
from app.models import Role, Stock, Trade, User


class ModelTradesTest(unittest.TestCase):
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

    def test_to_json(self):
        user = User(email='student@utdallas.edu', password='password')
        stock = Stock(name='Apple', ticker='AAPL', sector="Tech", is_active=True, year_high=1000.0, year_low=100.0)
        db.session.add(user)
        db.session.add(stock)
        db.session.commit()
        trade = Trade(stock_id=stock.id, user_id=user.id, quantity=1, price=1)
        db.session.add(trade)
        db.session.commit()

        with self.app.test_request_context('/'):
            trade_json = trade.to_json()
        self.assertEqual(trade.stock.ticker, trade_json['stock'], 'Stock tickers not equal')
        self.assertEqual(trade.user.username, trade_json['user'], 'Usernames not equal')
        self.assertEqual(trade.timestamp, trade_json['timestamp'], 'Timestamps are not equal')
        self.assertEqual(trade.quantity, trade_json['quantity'], 'Quantities not equal')
        self.assertEqual(trade.price, trade_json['price'], 'Prices are not equal')
        self.assertEqual('/api/v1/trades/' + str(trade.id), trade_json['url'])

    def test_from_json(self):
        user = User(username='student', email='student@utdallas.edu', password='password')
        stock = Stock(name='Apple', ticker='AAPL', sector="Tech", is_active=True, year_high=1000.0, year_low=100.0)
        db.session.add(user)
        db.session.add(stock)
        db.session.commit()
        trade1 = Trade(stock_id=stock.id, user_id=user.id, quantity=1, price=1)
        db.session.add(trade1)
        db.session.commit()
        with self.app.test_request_context('/'):
            trade_json = trade1.to_json()
        trade2 = Trade.from_json(trade_json)
        db.session.add(trade2)
        db.session.commit()
        self.assertEqual(trade1.stock, trade2.stock, 'Stocks not equal')
        self.assertEqual(trade1.user.username, trade2.user.username, 'Users not equal')
        self.assertEqual(trade1.quantity, trade2.quantity, 'Quantities not equal')
        self.assertEqual(trade1.price, trade2.price, 'Prices are not equal')
