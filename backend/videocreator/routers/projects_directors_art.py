from http.client import HTTPException
import json
from ninja import Router
from videocreator.schema import AICPActor, AICPLayer, AICPOutline
from videocreator.managers import (
    actors,
    projects,
    script as script_manager,
)
from videocreator.agents.art_director import ArtDirectorAgent
from videocreator.agents.layer_videoclip import VideoclipLayerAgent
from videocreator.agents.layer_voiceover import LayerVoiceoverAgent
from videocreator.managers import (
    director_art as art_manager,
    artists_storyboard as storyboard_manager,
    director_casting as casting_manager,
)
from videocreator.renderers import renderer

router = Router(
    tags=["directors"],
)


@router.post("/", summary="Run the art director on the script to generate the outline")
def generate_outline(request, project_id: str) -> AICPOutline:
    """
    Generate outline based on script/actors/characters
    """
    project = projects.get_project(project_id)
    script = script_manager.get_project_script(project_id)
    project.actors = (
        actors.list_actors() if len(project.actors) == 0 else project.actors
    )
    sb_artist = storyboard_manager.get_storyboard("improved_storyboard_artist")
    cast = casting_manager.get_cast_resolved(project_id)
    result = ArtDirectorAgent().generate(
        project=project, script=script, storyboard_artist=sb_artist, cast=cast
    )
    return result


@router.put("/", summary="Updates the outline with the user's input")
def update_outline(request, project_id: str, outline: AICPOutline):
    """
    Updates the outline with the user's input
    """
    art_manager.save_outline(project_id, outline)
    return outline


@router.get("/")
def get_outline(request, project_id: str):
    return art_manager.get_outline(project_id)


@router.post(
    "/sequences/{sequence_id}/scenes/{scene_id}/shots/{shot_id}/layers/",
    summary="Generate a layer for a shot",
)
def generate_layer(
    request,
    project_id: str,
    sequence_id: str,
    scene_id: str,
    shot_id: str,
    storyboard_artist_id: str,
    layer_type: str,
):
    """
    Generate a layer for a shot
    """
    project = projects.get_project(project_id)
    outline = art_manager.get_outline(project_id)
    sequence = outline.get_sequence_by_id(sequence_id)
    scene = sequence.get_scene_by_id(scene_id)
    shot = scene.get_shot_by_id(shot_id)
    cast = casting_manager.get_cast_resolved(project_id)
    if layer_type == "videoclip":
        storyboard_artist = storyboard_manager.get_storyboard(storyboard_artist_id)
        agent = VideoclipLayerAgent()
        return agent.generate(
            project=project, shot=shot, storyboard_artist=storyboard_artist
        )
    elif layer_type == "voiceover":
        if shot.dialog_character not in cast.keys():
            raise HTTPException(
                status_code=400,
                detail=f"Character {shot.dialog_character} not found in cast",
            )
        agent = LayerVoiceoverAgent()
        return agent.generate(project=project, shot=shot, cast=cast)


@router.post("/render", summary="Renders the outline")
def render_outline(request, project_id: str):
    """
    Renders the outline
    """
    outline = art_manager.get_outline(project_id)

    renderer.render_outline(outline, project_id)


@router.post("/sequences/{sequence_id}/render", summary="Renders a sequence")
def render_sequence(request, project_id: str, sequence_id: str):
    """
    Renders a sequence
    """
    outline = art_manager.get_outline(project_id)
    sequence = outline.get_sequence_by_id(sequence_id)
    renderer.render_sequence(sequence, project_id)


@router.post(
    "/sequences/{sequence_id}/scenes/{scene_id}/render", summary="Renders a scene"
)
def render_scene(request, project_id: str, sequence_id: str, scene_id: str):
    """
    Renders a scene
    """
    outline = art_manager.get_outline(project_id)
    sequence = outline.get_sequence_by_id(sequence_id)
    scene = sequence.get_scene_by_id(scene_id)
    renderer.render_scene(scene, project_id)


@router.post(
    "/sequences/{sequence_id}/scenes/{scene_id}/shots/{shot_id}/render",
    summary="Renders a shot",
)
def render_shot(request, project_id: str, sequence_id: str, scene_id: str, shot_id: str):
    """
    Renders a shot
    """
    outline = art_manager.get_outline(project_id)
    sequence = outline.get_sequence_by_id(sequence_id)
    scene = sequence.get_scene_by_id(scene_id)
    shot = scene.get_shot_by_id(shot_id)
    renderer.render_shot(shot, project_id)


@router.post(
    "/sequences/{sequence_id}/scenes/{scene_id}/shots/{shot_id}/layers/{layer_id}/render",
    summary="Renders a layer",
)
def render_layer(
    request, project_id: str, sequence_id: str, scene_id: str, shot_id: str, layer_id: str
):
    """
    Renders a layer
    """
    outline = art_manager.get_outline(project_id)
    sequence = outline.get_sequence_by_id(sequence_id)
    scene = sequence.get_scene_by_id(scene_id)
    shot = scene.get_shot_by_id(shot_id)
    layer = shot.get_layer_by_id(layer_id)
    renderer.render_layer(layer, project_id)
