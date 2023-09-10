
import os
import yaml
from backend import settings
from backend.utils.storage import read_file, write_file
from backend.managers import actors, projects, script

def get_cast(project_id):
    """Get the cast for a project."""
    file = read_file(os.path.join(settings.AICP_OUTPUT_DIR, f"{project_id}", "cast.yaml"))
    cast = yaml.load(file, Loader=yaml.FullLoader)
    return cast

def save_cast(project_id, cast: dict[str, str]):
    """Save the cast for a project, cast is a dict of character:actor pairs ."""

    all_characters_in_script = script.get_project_script(project_id).get_all_characters()
    all_characters_in_cast = []
    for actor_id, characters in cast.items():
        all_characters_in_cast.extend(characters)
        _ = actors.get_actor(actor_id) # Will raise an exception if actor is not found

    for character in all_characters_in_script:
        if character not in all_characters_in_cast:
            raise Exception(f"Character {character} is not in the cast")

    write_file(os.path.join(settings.AICP_OUTPUT_DIR, f"{project_id}", "cast.yaml"), yaml.safe_dump(cast))