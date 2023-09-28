"""Users manager"""

from django.contrib.auth import get_user_model, get_user

from users.schema import AICPRefreshTokenResult, AICPSignInResult, AICPUser
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

def sign_in_user(username: str, password: str):
    """Signs in a user."""
    try:
        user = get_user_model().objects.get(username=username)
        if user.check_password(password):
            refresh = RefreshToken.for_user(user)

            return AICPSignInResult(user=AICPUser.model_validate({
                "id": str(user.id),
                "username": user.username,
                "email": user.email
            }), access_token=str(refresh.access_token),  refresh_token=str(refresh))
    except get_user_model().DoesNotExist:
        pass
    return None

def refresh_token(token: str):
    """Refreshes a token."""
    refresh = RefreshToken(token)
    return AICPRefreshTokenResult(access_token=refresh.access_token, refresh_token=token)

def get_current_user():
    """Gets the current user."""
    return get_user()

def get_user_from_token(token: str):
    """Gets the user from a token."""
    access = AccessToken(token, verify=True)
    print(access)
    print(access.payload)
    try:
        return get_user_model().objects.get()
    except get_user_model().DoesNotExist:
        pass
    return None
