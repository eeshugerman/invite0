class PasswordStrengthError(Exception):
    pass


class UserAlreadyExistsError(Exception):
    pass


class PasswordNoUserInfoError(Exception):
    pass


class UserNotLoggedIn(Exception):
    pass


class CanNotUnsetFieldError(Exception):
    pass

