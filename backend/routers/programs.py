from fastapi import APIRouter
from backend.models import AICPProgram
from backend.managers import programs

router = APIRouter(
    prefix="/programs",
    tags=["programs"],
)


@router.get("/{program_id}")
def get_program(program_id: str) -> AICPProgram:
    """Get a program
    by reading yamls/programs directory
    the id is the filename
    """
    return programs.get_program(program_id)


@router.get("/")
def get_programs() -> list[AICPProgram]:
    """Get all programs
    by reading yamls/programs directory
    """
    return programs.list_programs()

