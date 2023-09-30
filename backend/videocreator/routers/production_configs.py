from ninja import Router 
from videocreator.schema import AICPProductionConfig 
from videocreator.managers import production_configs

router = Router(
    tags=["production_configs"],
)


@router.get("/{production_config_id}")
def get_production_config(request, production_config_id: str) -> AICPProductionConfig:
    """Get a production_config
    """
    return production_configs.get_production_config(production_config_id)


@router.get("/")
def get_production_configs(request) -> list[AICPProductionConfig]:
    """Get all production_configs
    """
    return production_configs.list_production_configs()
