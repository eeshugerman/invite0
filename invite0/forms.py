from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import Email, DataRequired, EqualTo, URL


class SignUpForm(FlaskForm):
    password = PasswordField('Password', validators=[
        DataRequired(),
        EqualTo('confirm_password', 'Passwords must match')
    ])
    confirm_password = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Create account')


class InviteForm(FlaskForm):
    email = StringField('Email', validators=[Email(), DataRequired()])
    submit = SubmitField('Send invititation')


class ProfileForm(FlaskForm):
    picture = StringField('Picture URL', validators=[URL()])
    nickname = StringField('Nickname')
    given_name = StringField('First Name')
    family_name = StringField('Last Name')
    submit = SubmitField('Save changes')
