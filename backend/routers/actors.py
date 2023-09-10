from fastapi import APIRouter
from backend.models import AICPActor 
from backend.managers import actors

router = APIRouter(
    prefix="/actors",
    tags=["actors"],
)

@router.get("/{actor_id}")
def get_actor(actor_id: str) -> AICPActor:
    """    
    Get an actor
        by reading yamls/cast/actors directory
        the id is the filename
    """
    return actors.get_actor(actor_id)
    
@router.get("/")
def get_actors() -> list[AICPActor]:
    """Get all actors
        by reading yamls/cast/actors directory
    """
    return actors.list_actors()
   