import re
import logging

from backend.models import AICPProject, AICPScript

logger = logging.getLogger(__name__)


def get_params_from_prompt(prompt: str) -> list[str]:
    """Given a text with formattable {} parameters, return them as a list."""
    # Regex to find anythin within single curly brackets
    # Do not match {{ }} as they are used for escaping
    regex = r"(?<!{){(?!{)(.*?)(?<!})}(?!})"
    matches = re.findall(regex, prompt)
    return matches


def resolve_param_from_video(video: AICPProject, param_name):
    """Given a parameter name, return its value from the user.
    params are defined like such:

    * `program__description`
    * `actors__bio`
    """
    # Split the param name by __
    params = param_name.split("__")
    # Get the first param
    first_param = params[0]
    # if the first param is actors, the concatenate the 2nd param for every actor
    if first_param == "actors":
        second_param = params[1]
        actors = video.actors
        return "\n".join(
            [
                ":".join([getattr(actor, "name"), getattr(actor, second_param, "")])
                for actor in actors
            ]
        )
    elif first_param == "program":
        program = video.program
        second_param = params[1]
        return getattr(program, second_param, "")
    elif first_param == "production_config":
        production_config = video.production_config
        second_param = params[1]
        return getattr(production_config, second_param, "")
    elif first_param == "script_schema":
        return AICPScript.schema_json(indent=2)
    else:
        logger.warning(f"Unknown param: {param_name}")
        return ""
