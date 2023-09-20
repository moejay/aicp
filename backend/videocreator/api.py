from videocreator.schema import AICPProject
from ninja import NinjaAPI, security
from videocreator.managers import projects

class GlobalAuth(security.HttpBearer):
    def authenticate(self, request, token):
        if token == "secret":
            return token

api = NinjaAPI()

@api.get("/projects", response=list[AICPProject])
def list_projects(request):
    """Returns a list of all projects."""
    return projects.list_projects()