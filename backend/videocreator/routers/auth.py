from ninja import Router
from videocreator.schema import AICPSignInCredentials, AICPUser, AICPSignInResult
from videocreator.managers import users
from django.http import Http404

router = Router(
    tags=["auth"],
)

@router.post("/sign-in", response=AICPSignInResult)
def sign_in(request, creads: AICPSignInCredentials) -> AICPSignInResult:
    """Sign in a user."""
    user = users.sign_in_user(creads.username, creads.password)
    if user is None:
        raise Http404("User does not exist or incorrect password.")
    return user
        