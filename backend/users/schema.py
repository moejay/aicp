from __future__ import annotations
from pydantic import BaseModel


class AICPUser(BaseModel):
    """Class encapsulating the user for an AICP video."""

    id: str
    username: str
    email: str | None = None


class AICPSignInCredentials(BaseModel):
    """Class encapsulating the sign in credentials for an AICP video."""

    username: str
    password: str


class AICPSignInResult(BaseModel):
    """Class encapsulating the sign in result for an AICP video."""

    user: AICPUser
    access_token: str
    refresh_token: str


class AICPRefreshTokenRequest(BaseModel):
    """Class encapsulating the refresh token request for an AICP video."""

    refresh_token: str


class AICPRefreshTokenResult(BaseModel):
    """Class encapsulating the refresh token result for an AICP video."""

    access_token: str
    refresh_token: str
