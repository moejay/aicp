from fastapi import APIRouter, HTTPException
from agents.research import ResearchAgent
from backend.managers import research
from backend.models import AICPResearch

router = APIRouter(
    prefix="/projects/{project_id}/research",
    tags=["projects_research"],
)

@router.get("/")
def get_research(project_id: str):
    research = research.get_project_research(project_id)
    return {"project_id": project_id, "research": research}

@router.put("/", summary="Updates research with the user's input")
def update_research(project_id: str, research: AICPResearch):
    research.save_project_research(project_id, research)
    return {"project_id": project_id, "research": research}

@router.post("/",summary="Generates research based on a prompt, does not save it")
def create_research(project_id: str, prompt: str) -> AICPResearch:
    result = ResearchAgent().generate(prompt)
    return AICPResearch(prompt=prompt, research=result)
