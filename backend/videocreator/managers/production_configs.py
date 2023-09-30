"""Module to manage Production Configs in the database."""
import os
import yaml
from videocreator.utils.storage import read_file
from videocreator.schema import AICPProductionConfig, AICPProgram
from django.conf import settings

PRODUCTION_CONFIG_PATH = os.path.join(settings.AICP_YAMLS_DIR, "production_configs")


def list_production_configs():
    """List all production configs."""
    production_configs = []

    for filename in os.listdir(PRODUCTION_CONFIG_PATH):
        if filename.endswith(".yaml"):
            # Load yaml
            program_contents = read_file(os.path.join(PRODUCTION_CONFIG_PATH, f"{filename}"))
            production_config = yaml.load(program_contents, Loader=yaml.FullLoader)
            production_configs.append(AICPProductionConfig.model_validate(production_config))

    return production_configs


def get_production_config(production_config_id):
    """Get a production config by id."""

    file = read_file(os.path.join(PRODUCTION_CONFIG_PATH, f"{production_config_id}.yaml"))
    production_config = yaml.load(file, Loader=yaml.FullLoader)
    return AICPProductionConfig.model_validate(production_config)
