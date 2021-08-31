from random import randint, uniform

from faker import Faker
from sqlalchemy.exc import IntegrityError

from . import db
from .models import User, Trade, Stock


def users(count=100):
    fake = Faker()
    i = 0
    while i < count:
        user = User(email=fake.email(),
                    username=fake.user_name(),
                    password='password',
                    confirmed=True,
                    name=fake.name(),
                    location=fake.city(),
                    about_me=fake.text(),
                    member_since=fake.past_date())
        db.session.add(user)
        try:
            db.session.commit()
            i += 1
        except IntegrityError:
            db.session.rollback()


def trades(count=100):
    fake = Faker()
    user_count = User.query.count()
    stock_count = Stock.query.count()
    for _ in range(count):
        user = User.query.offset(randint(0, user_count - 1)).first()
        stock = Stock.query.offset(randint(0, stock_count - 1)).first()
        trade = Trade(quantity=randint(0, 1000000),
                      price=round(uniform(stock.year_low, stock.year_high), 2),
                      timestamp=fake.past_date(),
                      stock=stock,
                      user=user)
        db.session.add(trade)
    db.session.commit()
