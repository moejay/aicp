"""Manages research for a project."""
import os
from backend.utils.storage import write_file, read_file
from backend.models import AICPResearch
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
    return research
