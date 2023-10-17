import os
import yaml
from django.conf import settings
from videocreator.utils.storage import read_file, write_file
from videocreator.schema import AICPStoryboardArtist


def get_storyboard(storyboard_id) -> AICPStoryboardArtist:
    """Get a storyboard by id."""
    file = read_file(
        os.path.join(
            settings.AICP_YAMLS_DIR,
            "cast",
            "storyboard_artists",
            f"{storyboard_id}.yaml",
        )
    )
    storyboard = yaml.load(file, Loader=yaml.FullLoader)
    return AICPStoryboardArtist.model_validate(storyboard)
