from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import Email, DataRequired, EqualTo

from invite0 import data
import invite0.config as conf


class SignUpForm(FlaskForm):
    # TODO: add other fields?
    password = PasswordField('Password', validators=[
        DataRequired(),
        EqualTo('confirm_password', 'Passwords must match')
    ])
    confirm_password = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Create account')


class InviteForm(FlaskForm):
    email = StringField('Email Address', validators=[Email(), DataRequired()])
    submit_single = SubmitField('Send invititation')


class BulkInviteForm(FlaskForm):
    emails = TextAreaField('Email Addresses', validators=[DataRequired()])
    submit_bulk = SubmitField('Send invititations')


# generate ProfileForm dynamically based on config.USER_FIELDS
profile_form_fields = {}
for field in conf.USER_FIELDS:
    field_data = data.ALL_USER_FIELDS[field]
    profile_form_fields[field] = StringField(
        field_data['label'],
        validators=field_data['validators']
    )
profile_form_fields['submit'] = SubmitField('Save changes')

ProfileForm = type('ProfileForm', (FlaskForm,), profile_form_fields)
