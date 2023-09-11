import json
from fastapi import APIRouter, HTTPException
from backend.models import AICPActor, AICPOutline
from backend.managers import (
    actors,
    projects,
    script as script_manager,
    casting as casting_manager,
)
from backend.agents.art_director import ArtDirectorAgent

router = APIRouter(
    prefix="/project/{project_id}/director/art",
    tags=["directors"],
)


@router.post("/", summary="Run the art director on the script to generate the outline")
def generate_outline(project_id: str) -> AICPOutline:
    """
    Generate outline based on script/actors/characters
    """
    project = projects.get_project(project_id)
    script = script_manager.get_project_script(project_id)
    project.actors = (
        actors.list_actors() if len(project.actors) == 0 else project.actors
    )
    result = ArtDirectorAgent().generate(project, script, project.actors)
    return result
