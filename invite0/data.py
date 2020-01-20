from wtforms.validators import URL

ALL_USER_FIELDS = {
    'phone_number': {'label': 'Phone Number', 'validators': []},
    'given_name':   {'label': 'First Name',   'validators': []},
    'family_name':  {'label': 'Last Name',    'validators': []},
    'name':         {'label': 'Full Name',    'validators': []},
    'nickname':     {'label': 'Nickname',     'validators': []},
    'picture':      {'label': 'Picture URL',  'validators': [URL()]},
    'username':     {'label': 'Username',     'validators': []},
}
