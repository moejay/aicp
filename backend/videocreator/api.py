from ninja import NinjaAPI, security
from videocreator.routers import actors as actors_router, programs as programs_router, projects as projects_router, auth as auth_router 


class GlobalAuth(security.HttpBearer):
    def authenticate(self, request, token):
        if token == "secret":
            return token

api = NinjaAPI()

api.add_router("/actors", actors_router.router, auth=GlobalAuth())
api.add_router("/programs", programs_router.router, auth=GlobalAuth())
api.add_router("/projects", projects_router.router, auth=GlobalAuth())
api.add_router("/auth", auth_router.router)
