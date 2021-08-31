from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User
import re


class ChangeEmailForm(FlaskForm):
    """
    Rendered by wtf.render_form()
    """
    email = StringField('New Email', validators=[DataRequired(), Length(1, 64),
                                                 Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Update Email Address')

    # noinspection PyMethodMayBeStatic
    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email already in use.')


class ChangePasswordForm(FlaskForm):
    """
    Rendered by wtf.render_form()
    """
    old_password = PasswordField('Old password', validators=[DataRequired()])
    password = PasswordField('New Password',
                             validators=[DataRequired(),
                                         EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm new password', validators=[DataRequired()])
    submit = SubmitField('Change password')


class LoginForm(FlaskForm):
    """
    Rendered by wtf.render_form()
    """
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')


class PasswordResetRequestForm(FlaskForm):
    """
    Rendered by wtf.render_form()
    """
    email = StringField('Email', validators=[DataRequired(),
                                             Length(1, 64),
                                             Email()])
    submit = SubmitField('Reset Password')


class PasswordResetForm(FlaskForm):
    """
    Rendered by wtf.render_form()
    """
    password = PasswordField('New Password', validators=[DataRequired(),
                                                         EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')


# noinspection PyMethodMayBeStatic
class RegistrationForm(FlaskForm):
    """
    Rendered by wtf.render_form()
    """
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField('Username',
                           validators=[DataRequired(),
                                       Length(1, 64),
                                       # Starts with a letter and only contains letters/numbers/underscores/dots
                                       Regexp('^[A-Za-z][A-Za-z0-9_.]*$',
                                              0,
                                              'Usernames must have only letters, numbers, dots or underscores')])
    password = PasswordField('Password',
                             validators=[DataRequired(),
                                         EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Password',
                              validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        """
        Called automatically by flask for custom validation
        :param field: value to validate
        :return: none if validation successful otherwise raises ValidationError
        """
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        """
        Called automatically by flask for custom validation
        :param field: value to validate
        :return: none if validation successful otherwise raises ValidationError
        """
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')

    def validate_password(self, field):
        """
        Called automatically by flask for custom validation
        :param field: value to validate
        :return: none if validation successful otherwise raises ValidationError
        """
        if not password_check(field.data):
            raise ValidationError('Password is not strong enough. Make sure 8+ characters, 1 digit or more, 1 symbol or more, 1 uppercase and 1 lowercase letter each')


def password_check(password):
    """
    Verify the strength of 'password'
    Returns a dict indicating the wrong criteria
    A password is considered strong if:
        8 characters length or more
        1 digit or more
        1 symbol or more
        1 uppercase letter or more
        1 lowercase letter or more
    """

    # calculating the length
    length_error = len(password) < 8

    # searching for digits
    digit_error = re.search(r"\d", password) is None

    # searching for uppercase
    uppercase_error = re.search(r"[A-Z]", password) is None

    # searching for lowercase
    lowercase_error = re.search(r"[a-z]", password) is None

    # searching for symbols
    symbol_error = re.search(r"[ !#$%&'()*+,-./[\\\]^_`{|}~"+r'"]', password) is None

    # overall result
    password_ok = not ( length_error or digit_error or uppercase_error or lowercase_error or symbol_error )

    return password_ok
