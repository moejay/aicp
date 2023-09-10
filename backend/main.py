from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv(".env")

from .routers import programs, projects, projects_research, actors, projects_script, cast
app = FastAPI()

app.include_router(programs.router)
app.include_router(actors.router)
app.include_router(projects.router)
app.include_router(projects_research.router)
app.include_router(projects_script.router)
app.include_router(cast.router)