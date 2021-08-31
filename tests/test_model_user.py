import unittest
import time
from datetime import datetime

from app import create_app, db
from app.models import AnonymousUser, Follow, Permission, Role, Stock, User, Watch
from typing import Final

STUDENT_EMAIL: Final = 'student@utdallas.edu'
TA_EMAIL: Final = 'ta@utdallas.edu'
TA_PASSWORD: Final = 'pa$$w0rd'


class ModelUserTest(unittest.TestCase):
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

    def test_password_setter(self):
        user = User(password='password')
        self.assertTrue(user.password_hash is not None)

    def test_no_password_getter(self):
        user = User(password='password')
        with self.assertRaises(AttributeError):
            user.password()

    def test_password_verify(self):
        user = User(password='password')
        self.assertTrue(user.verify_password('password'))
        self.assertFalse(user.verify_password(TA_PASSWORD))

    def test_password_salting(self):
        user = User(password='password')
        user2 = User(password='password')
        self.assertTrue(user.password_hash != user2.password_hash)

    def test_valid_account_confirmation_token(self):
        user = User(password='password')
        db.session.add(user)
        db.session.commit()
        token = user.generate_account_confirmation_token()
        self.assertTrue(user.confirm(token))

    def test_invalid_account_confirmation_token(self):
        user = User(password='password')
        user2 = User(password=TA_PASSWORD)
        db.session.add(user)
        db.session.add(user2)
        db.session.commit()
        token = user.generate_account_confirmation_token()
        self.assertFalse(user2.confirm(token))

    def test_expired_confirmation_token(self):
        user = User(password='password')
        db.session.add(user)
        db.session.commit()
        token = user.generate_account_confirmation_token(1)
        time.sleep(2)
        self.assertFalse(user.confirm(token))

    def test_valid_reset_token(self):
        user = User(password='password')
        db.session.add(user)
        db.session.commit()
        token = user.generate_password_reset_token()
        self.assertTrue(User.reset_password(token, TA_PASSWORD))
        self.assertTrue(user.verify_password(TA_PASSWORD))

    def test_invalid_reset_token(self):
        user = User(password='password')
        db.session.add(user)
        db.session.commit()
        token = user.generate_password_reset_token()
        self.assertFalse(User.reset_password(token + '0', TA_PASSWORD))
        self.assertTrue(user.verify_password('password'))

    def test_valid_email_change_token(self):
        user = User(email=TA_EMAIL, password='password')
        db.session.add(user)
        db.session.commit()
        token = user.generate_email_change_token(STUDENT_EMAIL)
        self.assertTrue(user.change_email(token))
        self.assertTrue(user.email == STUDENT_EMAIL)

    def test_invalid_email_change_token(self):
        user1 = User(email=TA_EMAIL, password='password')
        user2 = User(email=STUDENT_EMAIL, password=TA_PASSWORD)
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        token = user1.generate_email_change_token('professor@utdallas.edu')
        self.assertFalse(user2.change_email(token))
        self.assertTrue(user2.email == STUDENT_EMAIL)

    def test_duplicate_password_email_change_token(self):
        user1 = User(email=TA_EMAIL, password='password')
        user2 = User(email=STUDENT_EMAIL, password=TA_PASSWORD)
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        token = user2.generate_email_change_token(TA_EMAIL)
        self.assertFalse(user2.change_email(token))
        self.assertTrue(user2.email == STUDENT_EMAIL)

    def test_user_role(self):
        user = User(email=STUDENT_EMAIL, password='password')
        self.assertTrue(user.can(Permission.FOLLOW))
        self.assertTrue(user.can(Permission.COMMENT))
        self.assertTrue(user.can(Permission.WRITE))
        self.assertFalse(user.can(Permission.MODERATE))
        self.assertFalse(user.can(Permission.ADMIN))

    @staticmethod
    def get_user_with_role(role):
        return User(email=STUDENT_EMAIL, password='password', role=role)

    def test_moderator_role(self):
        user = self.get_user_with_role(Role.query.filter_by(name='Moderator').first())
        self.assertTrue(user.can(Permission.FOLLOW))
        self.assertTrue(user.can(Permission.COMMENT))
        self.assertTrue(user.can(Permission.WRITE))
        self.assertTrue(user.can(Permission.MODERATE))
        self.assertFalse(user.can(Permission.ADMIN))

    def test_administrator_role(self):
        user = self.get_user_with_role(Role.query.filter_by(name='Administrator').first())
        self.assertTrue(user.can(Permission.FOLLOW))
        self.assertTrue(user.can(Permission.COMMENT))
        self.assertTrue(user.can(Permission.WRITE))
        self.assertTrue(user.can(Permission.MODERATE))
        self.assertTrue(user.can(Permission.ADMIN))

    def test_anonymous_user(self):
        user = AnonymousUser()
        self.assertFalse(user.can(Permission.FOLLOW))
        self.assertFalse(user.can(Permission.COMMENT))
        self.assertFalse(user.can(Permission.WRITE))
        self.assertFalse(user.can(Permission.MODERATE))
        self.assertFalse(user.can(Permission.ADMIN))

    def test_timestamps(self):
        user = User(password='password')
        db.session.add(user)
        db.session.commit()
        self.assertTrue(
            (datetime.utcnow() - user.member_since).total_seconds() < 3)
        self.assertTrue(
            (datetime.utcnow() - user.last_seen).total_seconds() < 3)

    def test_ping(self):
        user = User(password='password')
        db.session.add(user)
        db.session.commit()
        time.sleep(2)
        last_seen_before = user.last_seen
        user.ping()
        self.assertTrue(user.last_seen > last_seen_before)

    def test_gravatar(self):
        user = User(email=STUDENT_EMAIL, password='password')
        with self.app.test_request_context('/'):
            gravatar = user.gravatar()
            gravatar_256 = user.gravatar(size=256)
            gravatar_pg = user.gravatar(rating='pg')
            gravatar_retro = user.gravatar(default='retro')
        self.assertTrue('https://secure.gravatar.com/avatar/390415e449db6f9332c93dbb50a5f10d' in gravatar)
        self.assertTrue('s=256' in gravatar_256)
        self.assertTrue('r=pg' in gravatar_pg)
        self.assertTrue('d=retro' in gravatar_retro)

    def test_follow(self):
        # Create users and assert user1 not following user2
        user1 = User(email=STUDENT_EMAIL, password='password')
        user2 = User(email=TA_EMAIL, password=TA_PASSWORD)
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        self.assertFalse(user1.is_following(user2))
        self.assertFalse(user1.is_followed_by(user2))

        # Assert user1 followed user2 with the correct timestamp recording it
        timestamp_before = datetime.utcnow()
        user1.follow(user2)
        db.session.add(user1)
        db.session.commit()
        timestamp_after = datetime.utcnow()
        self.assertTrue(user1.is_following(user2))
        self.assertFalse(user1.is_followed_by(user2))
        self.assertTrue(user2.is_followed_by(user1))
        self.assertTrue(user1.followed.count() == 2)
        self.assertTrue(user2.followers.count() == 2)
        follow = user1.followed.all()[-1]
        self.assertTrue(follow.followed == user2)
        self.assertTrue(timestamp_before <= follow.timestamp <= timestamp_after)
        follow = user2.followers.all()[0]
        self.assertTrue(follow.follower == user1)

        # Assert user1 unfollowed user2
        user1.unfollow(user2)
        db.session.add(user1)
        db.session.commit()
        self.assertTrue(user1.followed.count() == 1)
        self.assertTrue(user2.followers.count() == 1)
        self.assertTrue(Follow.query.count() == 2)

        # Assert when user is deleted that the follow record is deleted
        user2.follow(user1)
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        db.session.delete(user2)
        db.session.commit()
        self.assertTrue(Follow.query.count() == 1)

    def test_watch(self):
        # Create users and assert user1 not following user2
        user = User(email=STUDENT_EMAIL, password='password')
        stock = Stock(name='Apple', ticker='AAPL', sector="Tech", is_active=True, year_high=1000.0, year_low=100.0)
        db.session.add(user)
        db.session.add(stock)
        db.session.commit()
        self.assertFalse(user.is_watching(stock))
        self.assertFalse(stock.is_watched_by(user))

        # Assert user watched stock with timestamp recording it
        timestamp_before = datetime.utcnow()
        user.watch(stock)
        db.session.add(user)
        db.session.commit()
        timestamp_after = datetime.utcnow()
        self.assertTrue(user.is_watching(stock))
        self.assertTrue(stock.is_watched_by(user))
        self.assertTrue(user.watches.count() == 1)
        self.assertTrue(stock.users_watching.count() == 1)
        watch = user.watches.all()[-1]
        self.assertTrue(watch.stock == stock)
        self.assertTrue(timestamp_before <= watch.timestamp <= timestamp_after)
        watching = stock.users_watching.all()[-1]
        self.assertTrue(watching.user == user)

        # Assert user1 unfollowed user2
        user.unwatch(stock)
        db.session.add(user)
        db.session.commit()
        self.assertTrue(user.watches.count() == 0)
        self.assertTrue(stock.users_watching.count() == 0)
        self.assertTrue(Watch.query.count() == 0)

        # Assert when user is deleted that the watch record is deleted
        user.watch(stock)
        db.session.add(user)
        db.session.add(stock)
        db.session.commit()
        db.session.delete(user)
        db.session.commit()
        self.assertTrue(Watch.query.count() == 0)

    def test_to_json(self):
        user = User(username='student', email=STUDENT_EMAIL, password='password')
        db.session.add(user)
        db.session.commit()
        with self.app.test_request_context('/'):
            json_user = user.to_json()
        expected_keys = ['url', 'username', 'member_since', 'last_seen',
                         'trades_url', 'followed_trades_url', 'trade_count']
        self.assertEqual(sorted(expected_keys), sorted(json_user.keys()))
        self.assertEqual('/api/v1/users/' + user.username, json_user['url'])
