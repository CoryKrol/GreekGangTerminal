import unittest

from app import create_app, db
from app.models import Role, Stock, User, Watch


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
        user = User(username='student', email='student@utdallas.edu', password='password')
        stock = Stock(name='Apple', ticker='AAPL', sector="Tech", is_active=True, year_high=1000.0, year_low=100.0)
        db.session.add_all([stock, user])
        db.session.commit()
        watch = Watch(stock_id=stock.id, user_id=user.id)
        db.session.add(watch)
        db.session.commit()

        with self.app.test_request_context('/'):
            watch_json = watch.to_json()
        self.assertEqual(watch.stock.ticker, watch_json['stock'], 'Stock tickers not equal')
        self.assertEqual(watch.user.username, watch_json['user'], 'Usernames not equal')
        self.assertEqual('/api/v1/users/' + user.username + '/unwatch/' + stock.ticker, watch_json['url'])

    def test_from_json(self):
        user = User(username='student', email='student@utdallas.edu', password='password')
        stock = Stock(name='Apple', ticker='AAPL', sector="Tech", is_active=True, year_high=1000.0, year_low=100.0)
        db.session.add_all([stock, user])
        db.session.commit()
        watch1 = Watch(user=user, stock=stock)
        db.session.add(watch1)
        db.session.commit()
        with self.app.test_request_context('/'):
            watch_json = watch1.to_json()
        watch2 = Watch.from_json(watch_json)
        self.assertEqual(watch1.stock.id, watch2.stock_id, 'Stocks not equal')
        self.assertEqual(watch1.user.id, watch2.user_id, 'Users not equal')
