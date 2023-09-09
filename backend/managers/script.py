"""Manager for script operations"""

import os
import yaml

from backend.utils.storage import read_file
from backend.models import AICPScript, AICPScriptWriter
from backend import settings

SCRIPTWRITERS_PATH = os.path.join(settings.AICP_YAMLS_DIR, "cast", "script_writers")

def list_scriptwriters():
    """List all scriptwriters."""

    scriptwriters = []

    for filename in os.listdir(SCRIPTWRITERS_PATH):
        if filename.endswith(".yaml"):
            # Load yaml
            scriptwriters.append(filename.split(".")[0])
    
    return scriptwriters

def get_scriptwriter(scriptwriter_id):
    """Get a scriptwriter by id."""

    file = read_file(os.path.join( SCRIPTWRITERS_PATH, f"{scriptwriter_id.lower()}.yaml"))
    scriptwriter = yaml.load(file, Loader=yaml.FullLoader)
    return AICPScriptWriter.model_validate(scriptwriter)

def get_project_script(project_id: str):
    """Get script for a project."""

    script_dir = os.path.join(settings.AICP_OUTPUT_DIR, f"{project_id}", "script")
    script = AICPScript.model_validate(yaml.load(read_file(os.path.join(script_dir, "script.yaml")), Loader=yaml.FullLoader))
    return script

def save_project_script(project_id: str, script: AICPScript):
    """Save script to a project."""
    script_dir = os.path.join(settings.AICP_OUTPUT_DIR, f"{project_id}", "script")
    os.makedirs(script_dir, exist_ok=True)
    with open(os.path.join(script_dir, "script.yaml"), "w") as f:
        f.write(yaml.safe_dump(script.model_dump()))
