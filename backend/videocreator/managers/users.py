"""Users manager"""

from django.contrib.auth import get_user_model, get_user

from videocreator.schema import AICPSignInResult, AICPUser

def sign_in_user(username: str, password: str):
    """Signs in a user."""
    try:
        user = get_user_model().objects.get(username=username)
        if user.check_password(password):
            return AICPSignInResult(user=AICPUser.model_validate({
                "id": str(user.id),
                "username": user.username,
                "email": user.email
            }), token="secret")
    except get_user_model().DoesNotExist:
        pass
    return None

def get_current_user():
    """Gets the current user."""
    return get_user()