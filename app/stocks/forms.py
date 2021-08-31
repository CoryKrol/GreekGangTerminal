from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import BooleanField, DecimalField, FileField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError

from .. import photos
from ..models import Stock


class AddStockForm(FlaskForm):
    """
    Form for administrators to add new stock information
    Rendered by wtf.render_form()
    """
    ticker = StringField('Ticker', validators=[DataRequired(), Length(1, 5)])
    name = StringField('Name', validators=[DataRequired(), Length(1, 64)])
    photo = FileField('Logo', validators=[FileAllowed(photos, 'Images only'),
                                          FileRequired('You must add a company logo')])
    sector = StringField('Sector', validators=[DataRequired(), Length(1, 32)])
    year_high = DecimalField('52-Week High', places=2, validators=[DataRequired()])
    year_low = DecimalField('52-Week Low', places=2, validators=[DataRequired()])
    submit = SubmitField('Submit')

    # noinspection PyMethodMayBeStatic
    def validate_ticker(self, field):
        if Stock.query.filter_by(ticker=field.data).first():
            raise ValidationError('Ticker already in use.')

    def validate_year_high(self, field):
        if field.data < 0:
            raise ValidationError('52-Week High cannot be negative.')
        elif field.data < self.year_low.data:
            raise ValidationError('52-Week High cannot be > 52-Week Low.')

    def validate_year_low(self, field):
        if field.data < 0:
            raise ValidationError('52-Week Low cannot be negative.')
        elif field.data > self.year_high.data:
            raise ValidationError('52-Week Low cannot be > 52-Week High.')


class EditStockForm(FlaskForm):
    """
    Form for administrators to edit stock information
    Rendered by wtf.render_form()
    """
    ticker = StringField('Ticker', validators=[DataRequired(), Length(1, 5)])
    name = StringField('Name', validators=[DataRequired(), Length(1, 64)])
    photo = FileField('Logo', validators=[FileAllowed(photos, 'Images only')])
    active = BooleanField('Active')
    sector = StringField('Sector', validators=[DataRequired(), Length(1, 32)])
    year_high = DecimalField('52-Week High', places=2, validators=[DataRequired()])
    year_low = DecimalField('52-Week Low', places=2, validators=[DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, stock, *args, **kwargs):
        super(EditStockForm, self).__init__(*args, **kwargs)
        self.stock = stock

    def validate_ticker(self, field):
        if field.data != self.stock.ticker and Stock.query.filter_by(ticker=field.data).first():
            raise ValidationError('Ticker already in use.')

    def validate_year_high(self, field):
        if field.data < 0:
            raise ValidationError('52-Week High cannot be negative.')
        elif field.data < self.year_low.data:
            raise ValidationError('52-Week High cannot be > 52-Week Low.')

    def validate_year_low(self, field):
        if field.data < 0:
            raise ValidationError('52-Week Low cannot be negative.')
        elif field.data > self.year_high.data:
            raise ValidationError('52-Week Low cannot be > 52-Week High.')
