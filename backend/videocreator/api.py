from ninja import NinjaAPI, security
from users.users import get_user_from_token
from videocreator.routers import (
    actors as actors_router,
    programs as programs_router,
    projects as projects_router,
    production_configs as production_configs_router,
    projects_research as projects_research_router,
    projects_script as projects_script_router,
    #projects_directors_cast as projects_directors_cast_router,
    #projects_directors_art as projects_directors_art_router,
)


class GlobalAuth(security.HttpBearer):
    def authenticate(self, request, token):
        token = request.headers.get("authorization")
        if token:
            user = get_user_from_token(token.split(" ")[1])
            return token


def add_routers(api: NinjaAPI):
    api.add_router("/actors", actors_router.router, auth=GlobalAuth())
    api.add_router("/programs", programs_router.router, auth=GlobalAuth())
    api.add_router("/projects", projects_router.router, auth=GlobalAuth())
    api.add_router(
        "/production_configs", production_configs_router.router, auth=GlobalAuth()
    )
    api.add_router(
        "/projects/{project_id}/research",
        projects_research_router.router,
        auth=GlobalAuth(),
    )
    api.add_router(
        "/projects/{project_id}/script",
        projects_script_router.router,
        auth=GlobalAuth(),
    )
    # api.add_router(
    #     "/projects/{project_id}/directors/cast",
    #     projects_directors_cast_router.router,
    #     auth=GlobalAuth(),
    # )
    # api.add_router(
    #     "/projects/{project_id}/directors/art",
    #     projects_directors_art_router.router,
    #     auth=GlobalAuth(),
    # )

