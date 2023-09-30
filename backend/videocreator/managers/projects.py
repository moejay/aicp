"""Module to manage projects in the database."""
import os
import uuid
import yaml
from videocreator.utils.storage import read_file, write_file
from videocreator.schema import AICPProject, AICPProjectCreate
from django.conf import settings
from videocreator.managers import programs as programs_manager


def list_projects():
    """List all projects."""

    projects = []

    for filename in os.listdir(settings.AICP_OUTPUT_DIR):
        if os.path.isdir(
            os.path.join(settings.AICP_OUTPUT_DIR, filename)
        ) and os.path.exists(
            os.path.join(settings.AICP_OUTPUT_DIR, filename, "project.yaml")
        ):
            # Load yaml
            project_contents = read_file(
                os.path.join(settings.AICP_OUTPUT_DIR, f"{filename}", "project.yaml")
            )
            project = yaml.load(project_contents, Loader=yaml.FullLoader)
            projects.append(AICPProject.model_validate(project))

    return projects


def get_project(project_id):
    """Get a project by id."""

    file = read_file(
        os.path.join(settings.AICP_OUTPUT_DIR, f"{project_id}", "project.yaml")
    )
    project = yaml.load(file, Loader=yaml.FullLoader)
    return AICPProject.model_validate(project)


def create_project(new_project_request: AICPProjectCreate) -> AICPProject:
    """
    Create a project
    create a directory output/projects/{project_id}
    """
    new_project = AICPProject(
        id=str(uuid.uuid4()),
        name=new_project_request.name,
        description=new_project_request.description,
        program=programs_manager.get_program(new_project_request.program_id),
    )
    project_dir = os.path.join(settings.AICP_OUTPUT_DIR, f"{new_project.id}")
    os.makedirs(os.path.join(project_dir), exist_ok=False)
    # Write project as yaml to directory
    write_file(
        os.path.join(project_dir, "project.yaml"),
        yaml.safe_dump(new_project.model_dump()),
    )
    # Create logs directories in project directory
    os.makedirs(os.path.join(project_dir, "logs"), exist_ok=True)

    return new_project
