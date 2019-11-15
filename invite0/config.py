from environs import Env


env = Env()
env.read_env()

SERVER_NAME = env.str('INVITE0_DOMAIN')
SECRET_KEY = env.str('SECRET_KEY')

ORG_NAME = env.str('ORG_NAME')
INVITE_EXPIRATION_DAYS = env.decimal('INVITE_EXPIRATION_DAYS', default=5)
INVITE_PERMISSION = env.str('INVITE_PERMISSION', default='send:invitation')

MAIL_SERVER = env.str('MAIL_SERVER', default='localhost')
MAIL_PORT = env.str('MAIL_PORT', default=25)
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
