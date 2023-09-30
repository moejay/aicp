from ninja import Router
from videocreator.schema import AICPProject, AICPProjectCreate
from videocreator.managers import projects

router = Router(
    tags=["projects"],
)


@router.get("/")
def get_projects(request) -> list[AICPProject]:
    """Get all projects
    by reading output/projects directory
    """
    return projects.list_projects()


@router.get("/{project_id}")
def get_project(request, project_id: str) -> AICPProject:
    """Get a project
    by reading output/projects/{project_id}
    """
    return projects.get_project(project_id)


@router.post("/")
def create_project(request, new_project_request: AICPProjectCreate) -> AICPProject:
    """
    Create a project
    create a directory output/projects/{project_id}
    """
    print(request)
    print(new_project_request)
    return projects.create_project(new_project_request)
