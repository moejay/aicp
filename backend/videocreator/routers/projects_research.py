from ninja import Router
from videocreator.agents.research import ResearchAgent
from videocreator.managers import research as research_manager, projects
from videocreator.schema import AICPResearch

router = Router(
    tags=["projects_research"],
)


@router.get("/researchers")
def get_researchers(request):
    return research_manager.list_researchers()


@router.get("/")
def get_research(request, project_id: str):
    research = research_manager.get_project_research(project_id)
    return research


@router.put("/", summary="Updates research with the user's input")
def update_research(request, project_id: str, research: AICPResearch):
    research_manager.save_project_research(project_id, research)
    return research


@router.post("/", summary="Generates research based on a prompt, does not save it")
def create_research(request, project_id: str, researcher_id: str, prompt: str) -> AICPResearch:
    researcher = research_manager.get_researcher(researcher_id)
    project = projects.get_project(project_id)
    result = ResearchAgent(model=researcher.model, template=researcher.prompt).generate(
        project, prompt
    )
    return AICPResearch(prompt=prompt, result=result)
