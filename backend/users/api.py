from django.http import Http404
from ninja import Router, security
from users import users

from users.schema import (
    AICPRefreshTokenRequest,
    AICPSignInResult,
    AICPSignInCredentials,
    AICPRefreshTokenResult,
)

api = Router(
    tags=["users"],
)


@api.post("/sign-in", response=AICPSignInResult)
def sign_in(request, creds: AICPSignInCredentials) -> AICPSignInResult:
    """Sign in a user."""
    user = users.sign_in_user(creds.username, creds.password)
    if user is None:
        raise Http404("User does not exist or incorrect password.")
    return user


@api.post("/refresh", response=AICPRefreshTokenResult)
def refresh(request, refreshTokenRequest: AICPRefreshTokenRequest) -> str:
    """Refreshes a token."""
    return users.refresh_token(refreshTokenRequest.refresh_token)
