import os
import yaml
from backend import settings
from backend.utils.storage import read_file, write_file
from backend.managers import actors, projects, script


def get_cast(project_id) -> dict[str, str]:
    """Get the cast for a project."""
    file = read_file(
        os.path.join(settings.AICP_OUTPUT_DIR, f"{project_id}", "cast.yaml")
    )
    cast = yaml.load(file, Loader=yaml.FullLoader)
    return cast

def get_cast_resolved(project_id) -> dict[str, actors.AICPActor]:
    """Get the cast for a project, with actors resolved."""
    cast = get_cast(project_id)
    return {character: actors.get_actor(actor_id) for character, actor_id in cast.items()}


def save_cast(project_id, cast: dict[str, str]):
    """Save the cast for a project, cast is a dict of character:actor pairs ."""

    all_characters_in_script = script.get_project_script(
        project_id
    ).get_all_characters()

    for character, actor_id in cast.items():
        _ = actors.get_actor(actor_id)  # Will raise an exception if actor is not found
        if character not in all_characters_in_script:
            raise Exception(f"Character {character} is not in the cast")
    

    write_file(
        os.path.join(settings.AICP_OUTPUT_DIR, f"{project_id}", "cast.yaml"),
        yaml.safe_dump(cast),
    )
