from datetime import datetime, timedelta

from flask import current_app as app
from requests import Session


# TODO: Make this a module instead of a class. We only ever need one instance.
class Auth0ManagementAPIClient:
    """
    A light wrapper around `requests.session` for use with the Auth0 Management API

    - sets the base url
    - authenticates on first request
    - re-authenticates if token has expired
    """

    def __init__(self, domain, client_id, client_secret):
        self._domain = domain
        self._base_url = f'https://{domain}/api/v2'
        self._client_id = client_id
        self._client_secret = client_secret
        self._session = Session()
        self._auth_time = None
        self._auth = None

    def _authenticate(self):
        response = self._session.post(
            f'https://{self._domain}/oauth/token',
            data={
                'client_id': self._client_id,
                'client_secret': self._client_secret,
                'audience': f'https://{self._domain}/api/v2/',
                'grant_type': 'client_credentials',
            }
        )
        response.raise_for_status()
        self._auth = response.json()
        access_token = self._auth['access_token']
        self._session.headers['Authorization'] = f'Bearer {access_token}'
        self._auth_time = datetime.now()
        app.logger.info('Obtained access token for Management API.')

    def _access_token_expired(self) -> bool:
        expires_in = timedelta(seconds=self._auth['expires_in'])
        expiration_time = self._auth_time + expires_in
        buffer_ = timedelta(minutes=1)  # play it safe
        expired = datetime.now() > expiration_time - buffer_
        if expired:
            app.logger.info('Management API access token has expired.')
        return expired

    def _request(self, method, endpoint, raise_for_status=True, **kwargs):
        if self._auth is None or self._access_token_expired():
            self._authenticate()
        url = self._base_url + endpoint
        response = self._session.request(method, url, **kwargs)
        if raise_for_status:
            response.raise_for_status()
        return response

    def get(self, endpoint, **kwargs):
        return self._request('GET', endpoint, **kwargs)

    def post(self, endpoint, **kwargs):
        return self._request('POST', endpoint, **kwargs)

    def patch(self, endpoint, **kwargs):
        return self._request('PATCH', endpoint, **kwargs)
