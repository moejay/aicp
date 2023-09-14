import os
import yaml
from backend import settings
from backend.utils.storage import read_file, write_file
from backend.models import AICPStoryboardArtist

def get_storyboard(storyboard_id) -> AICPStoryboardArtist:
    """Get a storyboard by id."""
    file = read_file(
        os.path.join(settings.AICP_YAMLS_DIR, "cast", "storyboard_artists", f"{storyboard_id}.yaml")
    )
    storyboard = yaml.load(file, Loader=yaml.FullLoader)
    return AICPStoryboardArtist.model_validate(storyboard)

