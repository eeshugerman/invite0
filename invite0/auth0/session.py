from functools import wraps
from urllib.parse import urlencode
from typing import List, Dict

import requests
from requests.exceptions import HTTPError

from flask import session, redirect, url_for, request, render_template
from flask import current_app as app
from authlib.integrations.flask_client import OAuth

import invite0.config as conf
import invite0.auth0.management_client as auth0_mgmt
from invite0.auth0.exceptions import UserNotLoggedIn, CanNotUnsetFieldError

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
    """
    An abstraction over the Flask `session` and Auth0 APIs

    An instance of this class has no state of its own: the Flask `session`
    holds the state, which the instance merely reflects.

    There is no need to instantiate this class outside this module -- just
    import  `current_user` (instantiated below) -- but there is no harm in
    doing so because, as noted above, the state is shared by all instances
    in the session. This is essentially the borg pattern, though the shared
    state is kept in `session` rather than as a class attribute.

    This would arguably be better implemented as module, but then we wouldn't
    get to use `@property`, and `@property` is nice.

    Could we use Flask-Login instead? No, from what I can tell its not useful
    for OAuth login, which is what we're doing.
    """

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
        return auth0_mgmt.get(f'/users/{self.user_id}').json()

    # TODO: make this a property setter
    def update_profile(self, data):
        response = _management_api_client.patch(
            f'/users/{self.user_id}',
            data=data,
            raise_for_status=False
        )
        try:
            response.raise_for_status()
        except HTTPError as e:
            if response.json()['message'].startswith(
                "Payload validation error: 'String is too short (0 chars)"
            ):
                # TODO: Why doesn't Auth0 allow this? Is there a way around it?
                raise CanNotUnsetFieldError

    @property
    def permissions(self) -> List[str]:
        # TODO: give RBAC another try; it should work for this
        page_count = 0
        permissions = []
        while True:
            page = auth0_mgmt.get(
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

# TODO: Look into Flask-Dance -- i think it does what the next three functions do

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
    for an access token. The access token is used to call the /userinfo resource
    for the user ID and name, which are then stored in the session.

    See links in `login_redirect` docstring.
    """
    _oauth_client.authorize_access_token()  # raises if invalid
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
            # TODO: Use Flask error handling, return a 403
            # https://flask.palletsprojects.com/en/1.1.x/errorhandling/#error-handlers
            return render_template(
                'error.html',
                message='Your account lacks the permissions required to access this page.',
            )
        return decorated
    return decorator
