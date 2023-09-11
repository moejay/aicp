from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated
from backend.agents.research import ResearchAgent
from backend.managers import research as research_manager, projects
from backend.models import AICPResearch

router = APIRouter(
    prefix="/projects/{project_id}/research",
    tags=["projects_research"],
)


@router.get("/researchers")
def get_researchers():
    return research_manager.list_researchers()


@router.get("/")
def get_research(project_id: str):
    research = research_manager.get_project_research(project_id)
    return research


@router.put("/", summary="Updates research with the user's input")
def update_research(project_id: str, research: AICPResearch):
    research_manager.save_project_research(project_id, research)
    return research


@router.post("/", summary="Generates research based on a prompt, does not save it")
def create_research(project_id: str, researcher_id: str, prompt: str) -> AICPResearch:
    researcher = research_manager.get_researcher(researcher_id)
    project = projects.get_project(project_id)
    result = ResearchAgent(model=researcher.model, template=researcher.prompt).generate(
        project, prompt
    )
    return AICPResearch(prompt=prompt, result=result)
