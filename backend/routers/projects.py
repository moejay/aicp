from fastapi import APIRouter
import yaml
import os
from backend.utils.storage import read_file, write_file
from backend import settings
from backend.models import AICPProject

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)

@router.get("/{project_id}")
def get_project(project_id: str) -> AICPProject:
    """Get a project
        by reading output/projects/{project_id}
    """
    project_dir = os.path.join(settings.AICP_OUTPUT_DIR, f"{project_id}")
    project = yaml.load(read_file(os.path.join(project_dir, "project.yaml")), Loader=yaml.FullLoader)
    return AICPProject.model_validate(project)

@router.post("/")
def create_project(new_project: AICPProject) -> AICPProject:
    """
    Create a project
    create a directory output/projects/{project_id}
    """
    project_dir = os.path.join(settings.AICP_OUTPUT_DIR, f"{new_project.id}")
    os.makedirs(os.path.join(project_dir), exist_ok=False)
    # Write project as yaml to directory
    write_file(os.path.join(project_dir, "project.yaml"), yaml.safe_dump(new_project.model_dump()))
    return new_project
