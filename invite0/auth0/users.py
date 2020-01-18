from requests.exceptions import HTTPError
from flask import current_app as app

from invite0 import config as conf
from invite0.auth0._client import Auth0ManagementAPIClient
from invite0.auth0.exceptions import (
    PasswordStrengthError,
    PasswordNoUserInfoError,
    UserAlreadyExistsError,
)


_management_api_client = Auth0ManagementAPIClient(
    domain=conf.AUTH0_DOMAIN,
    client_id=conf.AUTH0_CLIENT_ID,
    client_secret=conf.AUTH0_CLIENT_SECRET,
)


def user_exists(email_address: str) -> bool:
    """Check if a user exists"""
    users = _management_api_client.get(
        '/users-by-email',
        params={'email': email_address}
    ).json()
    return bool(users)


def create_user(email_address: str, password: str):
    """Create a new user"""
    response = _management_api_client.post(
        '/users', data={
            'email': email_address,
            'password': password,
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
            app.logger.error(f'Failed to create account for {email_address}.', exc_info=e)
            raise e
    app.logger.info(f'Created user {email_address}!')
