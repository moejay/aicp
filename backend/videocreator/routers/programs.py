from ninja import Router 
from videocreator.schema import AICPProgram
from videocreator.managers import programs

router = Router(
    tags=["programs"],
)


@router.get("/{program_id}")
def get_program(request, program_id: str) -> AICPProgram:
    """Get a program
    by reading yamls/programs directory
    the id is the filename
    """
    return programs.get_program(program_id)


@router.get("/")
def get_programs(request) -> list[AICPProgram]:
    """Get all programs
    by reading yamls/programs directory
    """
    return programs.list_programs()
