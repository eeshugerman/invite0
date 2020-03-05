from functools import wraps
from urllib.parse import urlencode
from typing import List, Dict

import requests

from flask import session, redirect, url_for, request, render_template
from flask import current_app as app
from authlib.integrations.flask_client import OAuth

import invite0.config as conf
from invite0.auth0._client import Auth0ManagementAPIClient
from invite0.auth0.exceptions import UserNotLoggedIn

_management_api_client = Auth0ManagementAPIClient(
    domain=conf.AUTH0_DOMAIN,
    client_id=conf.AUTH0_CLIENT_ID,
    client_secret=conf.AUTH0_CLIENT_SECRET,
)

_oauth_client = OAuth(app).register(
    'auth0',
    client_id=conf.AUTH0_CLIENT_ID,
    client_secret=conf.AUTH0_CLIENT_SECRET,
    api_base_url=f'https://{conf.AUTH0_DOMAIN}',
    access_token_url=f'https://{conf.AUTH0_DOMAIN}/oauth/token',
    authorize_url=f'https://{conf.AUTH0_DOMAIN}/authorize',
    client_kwargs={'scope': 'openid profile email'},
)


class _CurrentUser:
    id_cookie = 'user_id'

    @property
    def user_id(self):
        if self.is_logged_in:
            return session[self.id_cookie]
        else:
            raise UserNotLoggedIn

    @property
    def is_logged_in(self):
        return self.id_cookie in session

    def log_in(self, user_id: str):
        session[self.id_cookie] = user_id

    def log_out(self):
        del session[self.id_cookie]

    @property
    def profile(self) -> Dict:
        return _management_api_client.get(f'/users/{self.user_id}').json()

    def update_profile(self, data):
        _management_api_client.patch(f'/users/{self.user_id}', data=data)

    @property
    def permissions(self) -> List[str]:
        # TODO: Use RBAC instead? I think I tried this but it didn't work?
        page_count = 0
        permissions = []
        while True:
            page = _management_api_client.get(
                f'/users/{self.user_id}/permissions',
                params={'page': page_count, 'include_totals': 'true'}
            ).json()
            permissions.extend(
                permission['permission_name']
                for permission in page['permissions']
            )
            if len(permissions) == page['total']:
                break
            page_count += 1
        return permissions

    def send_password_reset_email(self):
        requests.post(
            f'https://{conf.AUTH0_DOMAIN}/dbconnections/change_password',
            data={
                'email': self.profile['email'],
                'connection': 'Username-Password-Authentication'
            }
        )


current_user = _CurrentUser()


def login_redirect():
    """
    Initiate OAuth 2 Authorization Code Flow

    The user is redirected to Auth0 to log in and then is redirect back to
    our /login_callback with an authorization code.

    See:
      - https://github.com/auth0-samples/auth0-python-web-app/blob/master/01-Login/server.py
      - https://docs.authlib.org/en/latest/client/flask.html#routes-for-authorization
      - https://auth0.com/docs/flows/concepts/auth-code
      - https://auth0.com/docs/flows/guides/auth-code/call-api-auth-code

    """
    return _oauth_client.authorize_redirect(
        redirect_uri=url_for('login_callback', _external=True),
        audience=conf.AUTH0_AUDIENCE
    )


def handle_login_callback():
    """
    Complete authentication flow, store user info, and return the original route

    The authorization code is fetched from the request context and exchanged
    for an access token. The access token is used to call the /userinfo endpoint
    for the user ID and name, which are then stored in the session.

    See links in `login_redirect` docstring.
    """
    _oauth_client.authorize_access_token()
    userinfo = _oauth_client.get('userinfo').json()
    user_id = userinfo['sub']
    current_user.log_in(user_id)
    return session.pop('login_destination', None)


def logout_redirect():
    """
    Log out and redirect to /login

    User is redirected to Auth0 to log out and then sent back to our /login page
    """
    current_user.log_out()
    params = urlencode({
        'returnTo': url_for('login', _external=True),
        'client_id': conf.AUTH0_CLIENT_ID
    })
    return redirect(f'https://{conf.AUTH0_DOMAIN}/v2/logout?{params}')


def requires_login(func):
    """If user is not logged in, initiate authentication flow"""
    @wraps(func)
    def decorated(*args, **kwargs):
        if not current_user.is_logged_in:
            session['login_destination'] = request.path
            return redirect('/login')
        return func(*args, **kwargs)
    return decorated


def requires_permission(required_permission: str):
    """If user does not have `required_permission`, return an error message"""
    def decorator(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            if required_permission in current_user.permissions:
                return func(*args, **kwargs)
            app.logger.warning(f'A user lacking the `{required_permission}` permission '
                               f'tried to access {request.path}')
            return render_template(
                'error.html',
                message='Your account lacks the permissions required to access this page.',
                logout_button=True
            )
        return decorated
    return decorator
