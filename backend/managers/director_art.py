import os
import yaml
from backend import settings
from backend.utils.storage import read_file, write_file
from backend.models import AICPOutline


def get_outline(project_id) -> AICPOutline:
    """Get the outline for a project."""
    file = read_file(
        os.path.join(settings.AICP_OUTPUT_DIR, f"{project_id}", "outline.yaml")
    )
    outline = yaml.load(file, Loader=yaml.FullLoader)
    return AICPOutline.model_validate(outline)


def save_outline(project_id, outline: AICPOutline):
    """Save the outline for a project."""
    write_file(
        os.path.join(settings.AICP_OUTPUT_DIR, f"{project_id}", "outline.yaml"),
        yaml.safe_dump(outline.model_dump()),
    )
