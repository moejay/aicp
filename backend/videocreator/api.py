from ninja import NinjaAPI, security
from users.users import get_user_from_token
from videocreator.routers import actors as actors_router, programs as programs_router, projects as projects_router

class GlobalAuth(security.HttpBearer):
    def authenticate(self, request, token):
        print(request.COOKIES)
        print(request.headers)
        token = request.headers.get("authorization")
        print(token)
        if token:
            user = get_user_from_token(token.split(" ")[1])
            return token


def add_routers(api: NinjaAPI):
    api.add_router("/actors", actors_router.router, auth=GlobalAuth())
    api.add_router("/programs", programs_router.router, auth=GlobalAuth())
    api.add_router("/projects", projects_router.router, auth=GlobalAuth())
