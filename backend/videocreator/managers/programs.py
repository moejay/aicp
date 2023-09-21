"""Module to manage programs in the database."""
import os
import yaml
from videocreator.utils.storage import read_file
from videocreator.schema import AICPProgram
from django.conf import settings

PROGRAMS_PATH = os.path.join(settings.AICP_YAMLS_DIR, "programs")


def list_programs():
    """List all programs."""
    programs = []

    for filename in os.listdir(PROGRAMS_PATH):
        if filename.endswith(".yaml"):
            # Load yaml
            program_contents = read_file(os.path.join(PROGRAMS_PATH, f"{filename}"))
            program = yaml.load(program_contents, Loader=yaml.FullLoader)
            programs.append(AICPProgram.model_validate(program))

    return programs


def get_program(program_id):
    """Get a program by id."""

    file = read_file(os.path.join("programs", f"{program_id}.yaml"))
    program = yaml.load(file, Loader=yaml.FullLoader)
    return AICPProgram.model_validate(program)
