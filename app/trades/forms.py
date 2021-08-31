from flask_wtf import FlaskForm
from wtforms import DecimalField, IntegerField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError

from ..models import Stock, User


# noinspection PyMethodMayBeStatic
class BuyStockForm(FlaskForm):
    ticker = StringField('Ticker', validators=[DataRequired(), Length(1, 5)])
    price = DecimalField('Price', validators=[DataRequired()], places=2)
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def validate_price(self, field):
        if field.data < 0:
            raise ValidationError('Price cannot be negative.')

    def validate_quantity(self, field):
        if field.data < 1:
            raise ValidationError('Cannot buy less than 0 shares.')

    def validate_ticker(self, field):
        """TODO: Send email to admin to add stock manually"""
        if not Stock.query.filter_by(ticker=field.data).first():
            raise ValidationError('Stock not in system. An administrator has been notified.')


# noinspection PyMethodMayBeStatic
class EditTradeForm(FlaskForm):
    ticker = StringField('Ticker', validators=[DataRequired(), Length(1, 5)])
    user = StringField('Username', validators=[DataRequired(), Length(1, 64)])
    price = DecimalField('Price', validators=[DataRequired()], places=2)
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def validate_price(self, field):
        if field.data < 0:
            raise ValidationError('Price cannot be negative.')

    def validate_quantity(self, field):
        if field.data < 1:
            raise ValidationError('Cannot buy less than 0 shares.')

    def validate_ticker(self, field):
        """TODO: Send email to admin to add stock manually"""
        if not Stock.query.filter_by(ticker=field.data).first():
            raise ValidationError('Stock not in system. An administrator has been notified.')

    def validate_user(self, field):
        if not User.query.filter_by(username=field.data).first():
            raise ValidationError('User does not exist.')
