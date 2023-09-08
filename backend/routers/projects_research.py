from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
import os
from agents.research import ResearchAgent
from backend.utils.storage import write_file, read_file
from backend import settings

router = APIRouter(
    prefix="/projects/{project_id}/research",
    tags=["projects_research"],
)

async def get_research_directory(project_id: str):
    # Validate that the project exists
    project_dir = os.path.join(settings.AICP_OUTPUT_DIR, f"{project_id}")
    if not os.path.exists(project_dir):
        raise HTTPException(status_code=404, detail="Project not found")

    research_dir = os.path.join(project_dir, "research")
    os.makedirs(research_dir, exist_ok=True)
    return research_dir

@router.get("/")
def get_research(project_id: str, research_dir: Annotated[str, Depends(get_research_directory)]):
    research = read_file(os.path.join(research_dir, "research.txt"))
    return {"project_id": project_id, "research": research}

@router.put("/", summary="Updates research with the user's input")
def update_research(project_id: str, research: str, research_dir: Annotated[str, Depends(get_research_directory)]):
    write_file(os.path.join(research_dir, "research.txt"), research)
    return {"project_id": project_id, "research": research}

@router.post("/",summary="Generates research based on a prompt")
def create_research(project_id: str, prompt: str, research_dir: Annotated[str, Depends(get_research_directory)]) -> dict[str, str]:
    result = ResearchAgent().generate(prompt)
    write_file(os.path.join(research_dir, "research.txt"), result)
    return {"project_id": project_id, "research": result}
