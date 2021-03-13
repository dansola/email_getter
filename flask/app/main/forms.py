from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField
from wtforms.validators import DataRequired, Email


# Login screen
class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


# Home screen
class ScrapeForm(FlaskForm):
    email_folder = StringField('Email Folder to Search', validators=[DataRequired()])
    date = DateField('Search Until (mm/dd/yyyy)', validators=[DataRequired()], format='%m/%d/%Y')
    download = SubmitField('Download')
