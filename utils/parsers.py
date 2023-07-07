import os
import re

import contextlib
import wave
import logging
import yaml

from models import Scene, Video
from utils import utils

logger = logging.getLogger(__name__)
def get_voiceover_duration():
    """Get the duration of the voiceover script."""
    with contextlib.closing(wave.open(utils.VOICEOVER_WAV_FILE,'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
    return int(duration)

def get_script():
    """Retrieve the script from the script file."""
    with open(utils.SCRIPT, "r") as file:
        return yaml.load(file.read(), Loader=yaml.Loader)

def get_scenes():
    """Retrieve the scenes from the script file."""
    script = get_script()
    scenes = []
    for scene in script:
        scenes.append(
                Scene(
                        scene_title=scene['title'].strip(),
                        description=scene['description'].strip(),
                        content=scene['narrator'].strip(),
                        start_time=None,
                        duration=None
                    )
                )

    # Check if timecodes are available
    if not os.path.exists(utils.VOICEOVER_TIMECODES):
        return scenes
    timecodes = [
            float(t) for t in open(utils.VOICEOVER_TIMECODES, "r").readlines() if t.strip() != ""
            ]
    # Calculate duration of each scene
    for i, scene in enumerate(scenes):
        if i == len(timecodes) - 1:
            scene.duration = get_voiceover_duration() - timecodes[i]
        else:
            scene.duration = timecodes[i+1] - timecodes[i]
        scene.start_time = timecodes[i]

    return scenes

def get_params_from_prompt(prompt: str) -> list[str]:
    """Given a text with formattable {} parameters, return them as a list."""
    # Regex to find anythin within single curly brackets
    # Do not match {{ }} as they are used for escaping
    regex = r"(?<!{){(?!{)(.*?)(?<!})}(?!})"
    matches = re.findall(regex, prompt)
    return matches

def resolve_param_from_video(video: Video, param_name):
    """Given a parameter name, return its value from the user.
        params are defined like such:

        * `program__description`
        * `actors__character_bio`
    """
    # Split the param name by __ 
    params = param_name.split("__")
    # Get the first param
    first_param = params[0]
    # if the first param is actors, the concatenate the 2nd param for every actor
    if first_param == "actors":
        second_param = params[1]
        actors = video.actors
        return "\n".join([getattr(actor, second_param, "") for actor in actors])
    elif first_param == "program":
        program = video.program
        second_param = params[1]
        return getattr(program, second_param, "")
    else:
        logger.warning(f"Unknown param: {param_name}")
        return ""


