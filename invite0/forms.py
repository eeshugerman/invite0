from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import Email, DataRequired, EqualTo

import invite0.config as conf
from invite0 import data


class InviteForm(FlaskForm):
    email = StringField('Email Address', validators=[Email(), DataRequired()])
    submit_single = SubmitField('Send invititation')


class BulkInviteForm(FlaskForm):
    emails = TextAreaField('Email Addresses', validators=[DataRequired()])
    submit_bulk = SubmitField('Send invititations')


# generate ProfileForm and SignUpForm dynamically based on `config.[REQUIRED_]USER_FIELDS`
# TODO: could this be a good metaclass usecase?

def _generic_user_fields(required_only=False):
    form_fields = {}
    for field in (conf.REQUIRED_USER_FIELDS if required_only else conf.USER_FIELDS):
        field_data = data.ALL_USER_FIELDS[field]
        validators = field_data['validators']
        if field in conf.REQUIRED_USER_FIELDS:
            validators.append(DataRequired())
        form_fields[field] = StringField(
            field_data['label'],
            validators=validators
        )
    return form_fields

def _sign_up_form():
    fields = _generic_user_fields(required_only=True)
    fields['password'] = PasswordField('Password', validators=[
        DataRequired(),
        EqualTo('confirm_password', 'Passwords must match')
    ])
    fields['confirm_password'] = PasswordField('Confirm password', validators=[
        DataRequired()
    ])
    fields['submit'] = SubmitField('Create account')
    return type('SignUpForm', (FlaskForm,), fields)


def _profile_form():
    fields = _generic_user_fields()
    fields['submit'] = SubmitField('Save changes')
    return type('ProfileForm', (FlaskForm,), fields)

# the use of functions here is unnecessary, just doing this to provide some structure
SignUpForm = _sign_up_form()
ProfileForm = _profile_form()
