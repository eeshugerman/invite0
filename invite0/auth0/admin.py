from flask import current_app as app

from requests.exceptions import HTTPError

import invite0.config as conf
import invite0.auth0.management_client as auth0_mgmt
from invite0.auth0.exceptions import (
    PasswordStrengthError,
    UserAlreadyExistsError,
    PasswordNoUserInfoError,
)

def user_exists(email_address: str) -> bool:
    """Check if a user exists"""
    user = auth0_mgmt.get('/users-by-email', params={'email': email_address}).json()
    return bool(user)


def create_user(email_address: str, password: str, **extras):
    """Create a new user"""
    response = auth0_mgmt.post(
        '/users',
        data={
            'email': email_address,
            'password': password,
            **extras,
            'email_verified': 'true',
            'connection': 'Username-Password-Authentication'
        },
        raise_for_status=False
    )
    try:
        response.raise_for_status()
    except HTTPError as e:
        if response.json()['message'].startswith('PasswordStrengthError'):
            raise PasswordStrengthError
        elif response.json()['message'].startswith('PasswordNoUserInfoError'):
            raise PasswordNoUserInfoError
        elif response.status_code == 409:
            raise UserAlreadyExistsError
        else:
            app.logger.exception(f'Failed to create account for {email_address}.')
            raise e   # to be caught by caller
    app.logger.info(f'Created user {email_address}!')
