import json
from fastapi import APIRouter, HTTPException
from backend.models import AICPActor, AICPLayer, AICPOutline
from backend.managers import (
    actors,
    projects,
    script as script_manager,
)
from backend.agents.art_director import ArtDirectorAgent
from backend.agents.layer_videoclip import VideoclipLayerAgent
from backend.managers import director_art as art_manager, artists_storyboard as storyboard_manager

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
    sb_artist = storyboard_manager.get_storyboard("improved_storyboard_artist")
    result = ArtDirectorAgent().generate(project, script, project.actors, sb_artist)
    return result

@router.put("/", summary="Updates the outline with the user's input")
def update_outline(project_id: str, outline: AICPOutline):
    """
    Updates the outline with the user's input
    """
    art_manager.save_outline(project_id, outline)
    return outline 

@router.get("/")
def get_outline(project_id: str):
    return art_manager.get_outline(project_id)


@router.post("/sequences/{sequence_id}/scenes/{scene_id}/shots/{shot_id}/layers/", summary="Generate a layer for a shot")
def generate_layer(project_id: str, sequence_id: str, scene_id: str, shot_id: str, storyboard_artist_id: str):
    """
    Generate a layer for a shot
    """
    project = projects.get_project(project_id)
    outline = art_manager.get_outline(project_id)
    sequence = outline.get_sequence_by_id(sequence_id)
    scene = sequence.get_scene_by_id(scene_id)
    shot = scene.get_shot_by_id(shot_id)
    storyboard_artist = storyboard_manager.get_storyboard(storyboard_artist_id)
    agent = VideoclipLayerAgent()
    return agent.generate(project, shot, storyboard_artist)