from fastapi import APIRouter
from backend.models import AICPProject
from backend.managers import projects

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)

@router.get("/")
def get_projects() -> list[AICPProject]:
    """Get all projects
        by reading output/projects directory
    """
    return projects.list_projects()

@router.get("/{project_id}")
def get_project(project_id: str) -> AICPProject:
    """Get a project
        by reading output/projects/{project_id}
    """
    return projects.get_project(project_id)
    
@router.post("/")
def create_project(new_project: AICPProject) -> AICPProject:
    """
    Create a project
    create a directory output/projects/{project_id}
    """
    return projects.create_project(new_project)
    
