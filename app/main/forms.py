from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User


class SearchForm(FlaskForm):
    """
    Rendered by wtf.render_form()
    """
    query = StringField('Search query', validators=[DataRequired()])
    filter = SelectField('Filter', choices=[('stocks', 'Stocks'), ('users', 'Users')])
    submit = SubmitField('Search')
