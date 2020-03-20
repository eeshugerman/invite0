from environs import Env

from invite0 import data


env = Env()
env.read_env()

SERVER_NAME = env.str('INVITE0_DOMAIN')
ORG_NAME = env.str('ORG_NAME')
ORG_LOGO = env.url('ORG_LOGO', default=None).geturl()
USER_FIELDS = env.list('USER_FIELDS', default=['picture', 'nickname', 'given_name', 'family_name'])
INVITE_EXPIRATION_DAYS = env.decimal('INVITE_EXPIRATION_DAYS', default=5)
INVITE_PERMISSION = env.str('INVITE_PERMISSION', default='send:invitation')
WELCOME_URL = env.url('WELCOME_URL', default=None).geturl()
SECRET_KEY = env.str('SECRET_KEY')

MAIL_SERVER = env.str('MAIL_SERVER')
MAIL_PORT = env.str('MAIL_PORT')
MAIL_USE_TLS = env.bool('MAIL_USE_TLS', default=False)
MAIL_USE_SSL = env.bool('MAIL_USE_SSL', default=False)
MAIL_USERNAME = env.str('MAIL_USERNAME')
MAIL_PASSWORD = env.str('MAIL_PASSWORD')
MAIL_SENDER_NAME = env.str('MAIL_SENDER_NAME', default=None)
MAIL_SENDER_ADDRESS = env.str('MAIL_SENDER_ADDRESS')
MAIL_MAX_EMAILS = env.int('MAIL_MAX_EMAILS', default=None)

AUTH0_CLIENT_ID = env.str('AUTH0_CLIENT_ID')
AUTH0_CLIENT_SECRET = env.str('AUTH0_CLIENT_SECRET')
AUTH0_AUDIENCE = env.str('AUTH0_AUDIENCE')
AUTH0_DOMAIN = env.str('AUTH0_DOMAIN')


# validations
# --------------------------------------------------------------------------------------------------

# TODO: Use environs validation?
#  see: https://github.com/sloria/environs/blob/master/examples/validation_example.py

class ConfigError(Exception):
    def __init__(self, config_key, message):
        super().__init__(message)
        self.config_key = config_key

for field in USER_FIELDS:
    if field not in data.ALL_USER_FIELDS:
        raise ConfigError('USER_FIELDS', f'Unknown field: "{field}".')
