from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated
import json
from backend.agents.script import ScriptAgent
from backend.managers import (
    projects,
    script as script_manager,
    research as research_manager,
)
from backend.models import AICPScript

router = APIRouter(
    prefix="/projects/{project_id}/script",
    tags=["projects_script"],
)


@router.get("/scriptwriters")
def get_scriptwriters():
    return script_manager.list_scriptwriters()


@router.get("/")
def get_script(project_id: str):
    script = script_manager.get_project_script(project_id)
    return script


@router.put("/", summary="Updates script with the user's input")
def update_script(project_id: str, script: AICPScript):
    script_manager.save_project_script(project_id, script)
    return script


@router.post("/", summary="Generates script based on the existing research")
def generate_script(project_id: str, scriptwriter_id: str) -> AICPScript:
    scriptwriter = script_manager.get_scriptwriter(scriptwriter_id)
    project = projects.get_project(project_id)
    research = research_manager.get_project_research(project_id)
    result = ScriptAgent(
        model=scriptwriter.model, template=scriptwriter.prompt
    ).generate(project, research)

    return AICPScript.model_validate(json.loads(result))
