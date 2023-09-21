from ninja import Router, security
from videocreator.schema import AICPActor
from videocreator.managers import actors

router = Router(
    tags=["actors"],
)


@router.get("/{actor_id}")
def get_actor(request, actor_id: str) -> AICPActor:
    """
    Get an actor
        by reading yamls/cast/actors directory
        the id is the filename
    """
    return actors.get_actor(actor_id)


@router.get("/")
def get_actors(request) -> list[AICPActor]:
    """Get all actors
    by reading yamls/cast/actors directory
    """
    return actors.list_actors()
