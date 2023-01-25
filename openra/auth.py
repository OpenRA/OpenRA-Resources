

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User


def set_session_to_remember_auth(request, remember: bool):
    if remember:
        request.session.set_expiry(None)
    else:
        request.session.set_expiry(0)


def try_login(request):
    credentials = _extract_credentials(request)
    user = _authenticate_credentials(credentials)
    _ensure_active_user(user)
    login(request, user)


class Credentials:
    username: str
    password: str

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def are_both_provided(self):
        return self.username != '' and self.password != ''


def _extract_credentials(request):
    credentials = Credentials(
        request.POST.get('ora_username', '').strip(),
        request.POST.get('ora_password', '').strip()
    )
    if not credentials.are_both_provided():
        raise ExceptionLoginFailed('incorrect')
    return credentials


def _authenticate_credentials(credentials: Credentials):
    user = authenticate(
        username=credentials.username,
        password=credentials.password
    )
    if user is None:
        raise ExceptionLoginFailed('incorrect')
    return user


def _ensure_active_user(user: User):
    if not user.is_active:
        raise ExceptionLoginFailed('inactive')


class ExceptionLoginFailed(Exception):

    reason: str

    def __init__(self, reason: str):
        self.reason = reason
