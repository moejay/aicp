from fastapi import APIRouter, HTTPException
from backend.managers import (
    actors,
    director_casting as casting_manager,
    projects,
    script as script_manager,
)
from backend.agents.casting_director import CastingDirectorAgent

router = APIRouter(
    prefix="/project/{project_id}/director/cast",
    tags=["directors"],
)


@router.post("/", summary="Casts actors based on the project's script")
def cast_actors(project_id: str):
    """
    Generate cast based on script/actors/characters
    """
    project = projects.get_project(project_id)
    script = script_manager.get_project_script(project_id)
    project.actors = (
        actors.list_actors() if len(project.actors) == 0 else project.actors
    )
    result = CastingDirectorAgent().generate(project, script, project.actors)
    return result 


@router.put("/", summary="Updates the cast with the user's input")
def update_cast(project_id: str, cast: dict[str, list[str]]):
    """
    Updates the cast with the user's input
    """
    try:
        casting_manager.save_cast(project_id, cast)
        return cast
    except actors.ActorNotFound as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
def get_cast(project_id: str):
    return casting_manager.get_cast(project_id)
