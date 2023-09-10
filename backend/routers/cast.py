import json
from fastapi import APIRouter
from backend.models import AICPActor 
from backend.managers import actors, projects, script as script_manager
from backend.agents.casting_director import CastingDirectorChain
from backend.utils.llms import get_llm_instance

router = APIRouter(
    prefix="/project/{project_id}/director",
    tags=["directors"],
)

@router.post("/cast", summary="Casts actors based on the project's script")
def cast_actors(project_id: str):
    """
    Generate cast based on script/actors/characters
    """
    project = projects.get_project(project_id)
    script = script_manager.get_project_script(project_id)
    project.actors = actors.list_actors() if len(project.actors) == 0 else project.actors
    chain = CastingDirectorChain(llm=get_llm_instance("openai-gpt-4"))
    result = chain.run({"project": project, "script": script, "actors": project.actors})
    print(result)
    return json.loads(result)
