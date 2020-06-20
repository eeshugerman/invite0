"""
A light wrapper around `requests.session` for use with the Auth0 Management API

The public functions (`get`, `post`, and `patch`) may be used as
normal, except that the following is handled automatically:
- base url
- authentication on first request
- re-authentication if token has expired

Some might implement this as a class, but this would be misguided imo because
we only want one instance and do not need inheritance. That said, this approach
does have drawbacks for testing, and if we're ever to add support for other IdPs
then we'll probably want inheritance.
"""
from datetime import datetime, timedelta
from types import SimpleNamespace

from flask import current_app as app
from requests import Session

import invite0.config as conf


_self = SimpleNamespace(
    session=Session(),
    token_expiration_time=None
)

def _authenticate():
    response = _self.session.post(f'https://{conf.AUTH0_DOMAIN}/oauth/token', data=dict(
        client_id=conf.AUTH0_CLIENT_ID,
        client_secret=conf.AUTH0_CLIENT_SECRET,
        audience=f'https://{conf.AUTH0_DOMAIN}/api/v2/',
        grant_type='client_credentials',
    ))
    response.raise_for_status()
    response = response.json()
    _self.token_expiration_time = datetime.now() + timedelta(seconds=response['expires_in'])
    _self.session.headers['Authorization'] = 'Bearer {}'.format(response['access_token'])
    app.logger.info('Obtained access token for Management API.')


def _token_has_expired() -> bool:
    buffer_ = timedelta(seconds=30)  # play it safe
    return datetime.now() > _self.token_expiration_time - buffer_


def _request(method, resource, raise_for_status=True, **kwargs):
    is_first_request = _self.token_expiration_time is None
    if is_first_request or _token_has_expired():
        _authenticate()

    url = f'https://{conf.AUTH0_DOMAIN}/api/v2{resource}'
    response = _self.session.request(method, url, **kwargs)
    if raise_for_status:
        response.raise_for_status()
    return response


def get(resource, **kwargs):
    return _request('GET', resource, **kwargs)


def post(resource, **kwargs):
    return _request('POST', resource, **kwargs)


def patch(resource, **kwargs):
    return _request('PATCH', resource, **kwargs)
