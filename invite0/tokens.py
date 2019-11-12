from itsdangerous import URLSafeTimedSerializer

import invite0.config as conf


_serializer = URLSafeTimedSerializer(conf.SECRET_KEY)


def generate_token(email_address: str) -> str:
    """
    Generate a tamper-proof and URL-safe token encoding email
    address and current time.

    NOTE: Payload is _not_ encrypted! It is merely signed.
    """
    return _serializer.dumps(email_address)


def read_token(token: str) -> str:
    """
    Checks that...
      - we generated the token
      - token has not been tampered with
      - token is not expired

    If all checks pass, payload (ie the email address) is
    deserialized and returned.
    """

    max_age_seconds = conf.INVITE_EXPIRATION_DAYS * 60 * 60 * 24
    return _serializer.loads(token, max_age=max_age_seconds)
