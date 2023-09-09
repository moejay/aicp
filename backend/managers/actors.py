"""Module to manage actors in the database."""
import os
import yaml
from backend.utils.storage import read_file
from backend.models import AICPActor
from backend import settings

ACTORS_PATH = os.path.join(settings.AICP_YAMLS_DIR, "cast", "actors")

def list_actors():
    """List all actors."""

    actors = []

    for filename in os.listdir(ACTORS_PATH):
        if filename.endswith(".yaml"):
            # Load yaml
            actor_contents = read_file(os.path.join( ACTORS_PATH, f"{filename}"))
            actor = yaml.load(actor_contents, Loader=yaml.FullLoader)
            actors.append(AICPActor.model_validate(actor))
    
    return actors

def get_actor(actor_id):
    """Get an actor by id."""

    file = read_file(os.path.join( ACTORS_PATH, f"{actor_id.lower()}.yaml"))
    actor = yaml.load(file, Loader=yaml.FullLoader)
    return AICPActor.model_validate(actor)
