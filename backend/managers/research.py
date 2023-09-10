"""Manages research for a project."""
import os
import yaml
from backend.utils.storage import write_file, read_file
from backend.models import AICPResearch, AICPResearcher
from backend import settings

def save_project_research(project_id: str, research: AICPResearch):
    """Save research to a project."""
    research_dir = os.path.join(settings.AICP_OUTPUT_DIR, f"{project_id}", "research")
    os.makedirs(research_dir, exist_ok=True)
    write_file(os.path.join(research_dir, "research.txt"), research)

def get_project_research(project_id: str):
    """Get research for a project."""
    research_dir = os.path.join(settings.AICP_OUTPUT_DIR, f"{project_id}", "research")
    research = read_file(os.path.join(research_dir, "research.txt"))
    return AICPResearch.model_validate(yaml.load(research, Loader=yaml.FullLoader))

def list_researchers():
    """List all available researchers, but not the actual template (At least not now, not for all users)"""
    researchers = []
    for filename in os.listdir(os.path.join(settings.AICP_YAMLS_DIR,"cast", "researchers")):
        if filename.endswith(".yaml"):
            researchers.append(filename)
    return researchers

def get_researcher(researcher_id: str):
    """Get a researcher by id."""
    file = read_file(os.path.join(settings.AICP_YAMLS_DIR,"cast", "researchers", f"{researcher_id.lower()}.yaml"))
    researcher = AICPResearcher.model_validate(yaml.load(file, Loader=yaml.FullLoader))
    return researcher 