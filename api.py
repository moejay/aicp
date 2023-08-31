from fastapi import FastAPI
from models import AICPProject

app = FastAPI()

@app.post("/projects")
def create_project(new_project: AICPProject):
    return {"message": "Project has been created"}

@app.get("/projects/{project_id}")
def get_project(project_id: str):
    return {"project_id": project_id}

