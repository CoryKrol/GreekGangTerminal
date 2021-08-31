import hashlib
from datetime import datetime
from typing import Final

from flask import abort, current_app, url_for
from flask_login import AnonymousUserMixin, UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash, check_password_hash

from . import db, login_manager, whooshee
from .exceptions import ValidationError

CASCADE: Final = 'all, delete-orphan'
USERS_ID: Final = 'users.id'


# noinspection PyMethodMayBeStatic, PyUnusedLocal
class AnonymousUser(AnonymousUserMixin):
    """
    Class to hold the permission of unauthenticated users so we can check permissions without having to do a login check
    """

    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser


class Permission:
    """By using permissions of power 2 permissions can be combined with addition"""
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    def __repr__(self):
        return '<Role %r>' % self.name

    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            'Moderator': [Permission.FOLLOW, Permission.COMMENT,
                          Permission.WRITE, Permission.MODERATE],
            'Administrator': [Permission.FOLLOW, Permission.COMMENT,
                              Permission.WRITE, Permission.MODERATE,
                              Permission.ADMIN],
        }
        default_role = 'User'
        for role_dict in roles:
            role = Role.query.filter_by(name=role_dict).first()
            if role is None:
                role = Role(name=role_dict)
            role.reset_permissions()
            for perm in roles[role_dict]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        """Use bitwise AND to check for existence of permission for user"""
        return self.permissions & perm == perm


class Watch(db.Model):
    __tablename__ = 'watches'
    user_id = db.Column(db.Integer, db.ForeignKey(USERS_ID),
                        primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'),
                         primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_json(self):
        return {
            'url': url_for('api.user_unwatch_stock', username=self.user.username, ticker=self.stock.ticker),
            'user': self.user.username,
            'stock': self.stock.ticker
        }

    @staticmethod
    def from_json(json):
        username = json.get('user')
        if username is None or username == '':
            raise ValidationError('new watchlist entry does not have a username')
        ticker = json.get('stock')
        if ticker is None or ticker == '':
            raise ValidationError('new watchlist entry does not have a stock ticker')
        user = User.find_first_by_username(username=username)
        if user is None:
            raise ValidationError('user does not exist')
        stock = Stock.query.filter_by(ticker=ticker).first()
        if stock is None:
            raise ValidationError('stock does not exist')
        return Watch(user_id=user.id, stock_id=stock.id)


@whooshee.register_model('name', 'ticker', 'sector')
class Stock(db.Model):
    __tablename__ = 'stocks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    ticker = db.Column(db.String(5), unique=True, index=True)
    sector = db.Column(db.String(32), index=True)
    is_active = db.Column(db.Boolean, default=True)
    photo_filename = db.Column(db.String(256))
    year_high = db.Column(db.Float)
    year_low = db.Column(db.Float)
    trades = db.relationship('Trade', backref='stock', lazy='dynamic')
    users_watching = db.relationship('Watch',
                                     foreign_keys=[Watch.stock_id],
                                     backref=db.backref('stock', lazy='joined'),
                                     lazy='dynamic',
                                     cascade=CASCADE)

    def is_watched_by(self, user):
        if user.id is None:
            return False
        return self.users_watching.filter_by(user_id=user.id).first() is not None

    def to_json(self):
        return {
            'url': url_for('api.get_stock', ticker=self.ticker),
            'name': self.name,
            'ticker': self.ticker,
            'sector': self.sector,
            'is_active': self.is_active,
            'year_high': self.year_high,
            'year_low': self.year_low
        }

    @staticmethod
    def from_json(json):
        name = json.get('name')
        if name is None or name == '':
            raise ValidationError('stock does not have a name')
        ticker = json.get('ticker')
        if ticker is None or ticker == '':
            raise ValidationError('stock does not have a ticker')
        sector = json.get('sector')
        if sector is None or sector == '':
            raise ValidationError('stock does not have a sector')
        year_high = json.get('year_high') or 0
        if year_high < 0.0:
            raise ValidationError('52-week high cannot be negative')
        year_low = json.get('year_low') or 0
        if year_low < 0.0:
            raise ValidationError('52-week low cannot be negative')
        if year_high < year_low:
            raise ValidationError('52-week low cannot be larger than 52-week high')
        return Stock(name=name,
                     ticker=ticker,
                     sector=sector,
                     year_high=year_high,
                     year_low=year_low)


class Trade(db.Model):
    __tablename__ = 'trades'
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'))
    user_id = db.Column(db.Integer, db.ForeignKey(USERS_ID))
    timestamp = db.Column(db.DateTime(), index=True, default=datetime.utcnow)
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)

    def to_json(self):
        return {
            'url': url_for('api.get_trade', trade_id=self.id),
            'stock': self.stock.ticker,
            'user': self.user.username,
            'timestamp': self.timestamp,
            'quantity': self.quantity,
            'price': self.price
        }

    @staticmethod
    def from_json(json):
        quantity = json.get('quantity')
        if quantity is None or quantity == '':
            raise ValidationError('trade does not have a quantity.')
        price = json.get('price')
        if price is None or price == '':
            raise ValidationError('trade does not have a price.')
        username = json.get('user')
        if username is None or username == '':
            raise ValidationError('trade does not have a user.')
        ticker = json.get('stock')
        if ticker is None or ticker == '':
            raise ValidationError('trade does not have a stock.')
        stock = Stock.query.filter_by(ticker=ticker).first()
        if stock is None:
            raise ValidationError('stock does not exist')
        user = User.find_first_by_username(username=username)
        if user is None:
            raise ValidationError('user does not exist')

        return Trade(stock_id=stock.id,
                     user_id=user.id,
                     quantity=quantity,
                     price=price)


class Follow(db.Model):
    __tablename__ = 'follows'
    followed_id = db.Column(db.Integer, db.ForeignKey(USERS_ID),
                            primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey(USERS_ID),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


@whooshee.register_model('username', 'email', 'name', 'about_me', 'location')
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    trades = db.relationship('Trade', backref='user', lazy='dynamic')
    watches = db.relationship('Watch',
                              foreign_keys=[Watch.user_id],
                              backref=db.backref('user', lazy='joined'),
                              lazy='dynamic',
                              cascade=CASCADE)
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade=CASCADE)
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade=CASCADE)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['GREEK_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()
        self.follow(self)

    def __repr__(self):
        return '<User %r>' % self.username

    @property
    def password(self):
        raise AttributeError('Password cannot be read.')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_account_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except SignatureExpired:
            return False
        except BadSignature:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_password_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id}).decode('utf-8')

    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except SignatureExpired:
            return False
        except BadSignature:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps(
            {'change_email': self.id, 'new_email': new_email}).decode('utf-8')

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except SignatureExpired:
            return False
        except BadSignature:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = self.gravatar_hash()
        db.session.add(self)
        return True

    def can(self, perm):
        """Returns true if the requested permission is contained within the user's role"""
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        """Returns true if the user's role contains the administrator position"""
        return self.can(Permission.ADMIN)

    def ping(self):
        """Called by @auth.before_app_request to update last_login field"""
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()

    def gravatar(self, size=100, default='identicon', rating='g'):
        url = 'https://secure.gravatar.com/avatar'
        grav_hash = self.avatar_hash or self.gravatar_hash()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(url=url,
                                                                     hash=grav_hash,
                                                                     size=size,
                                                                     default=default,
                                                                     rating=rating)

    def follow(self, user):
        if not self.is_following(user):
            follow = Follow(follower=self, followed=user)
            db.session.add(follow)

    def unfollow(self, user):
        follow = self.followed.filter_by(followed_id=user.id).first()
        if follow:
            db.session.delete(follow)

    def is_following(self, user):
        if user.id is None:
            return False
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        if user.id is None:
            return False
        return self.followers.filter_by(follower_id=user.id).first() is not None

    def get_followers_pagination(self, page_request):
        return self.follows.paginate(page_request.args.get('page', 1, type=int),
                                     per_page=current_app.config['FOLLOWERS_PER_PAGE'],
                                     error_out=False)

    def get_followed_pagination(self, page_request):
        return self.followed.paginate(page_request.args.get('page', 1, type=int),
                                      per_page=current_app.config['FOLLOWERS_PER_PAGE'],
                                      error_out=False)

    def is_watching(self, stock):
        if stock.id is None:
            return False
        return self.watches.filter_by(stock_id=stock.id).first() is not None

    def watch(self, stock):
        if not self.is_watching(stock):
            watch = Watch(user=self, stock=stock)
            db.session.add(watch)
            db.session.commit()

    def unwatch(self, stock):
        watch = self.watches.filter_by(stock_id=stock.id).first()
        if watch:
            db.session.delete(watch)
            db.session.commit()

    @property
    def followed_trades(self):
        return Trade.query.join(Follow, Follow.followed_id == Trade.user_id).filter(Follow.follower_id == self.id)

    @staticmethod
    def add_self_follows():
        """Used to upgrade existing database instances to the new model with user following"""
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    def generate_auth_token(self, expiration):
        serializer = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return serializer.dumps({'id': self.id}).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        serializer = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = serializer.loads(token)
        except SignatureExpired:
            return None
        except BadSignature:
            return None
        return User.query.get(data['id'])

    @staticmethod
    def find_first_by_username(username):
        return User.query.filter_by(username=username).first()

    @staticmethod
    def find_by_username_or_404(username):
        user = User.find_first_by_username(username=username)
        if user is None:
            abort(404)
        return user

    def to_json(self):
        return {
            'url': url_for('api.get_user', username=self.username),
            'username': self.username,
            'member_since': self.member_since,
            'last_seen': self.last_seen,
            'trades_url': url_for('api.get_user_trades', username=self.username),
            'followed_trades_url': url_for('api.get_user_followed_trades', username=self.username),
            'trade_count': self.trades.count()
        }


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
