import os
import json
import re

import contextlib
import wave
import logging
import yaml

from models import Scene, SceneDialogue, Video, Actor, VOLine
from utils import utils

logger = logging.getLogger(__name__)


def get_voiceover_duration():
    """Get the duration of the voiceover script."""
    with contextlib.closing(wave.open(utils.VOICEOVER_WAV_FILE, "r")) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
    return int(duration)


def get_voiceover_lines():
    """Get the successful takes of the recorded VO lines."""
    # List all the files in the voiceover directory
    files = os.listdir(utils.VOICEOVER_PATH)
    # Filter only the files that end with .json and don't have the word "take" in them
    files = [
        file
        for file in files
        if file.endswith(".json") and "take" not in file  # Change to json later
    ]
    vo_lines = []
    # The file name is of the pattern `scene_{scene_index}_line_{line_index}_{sentence_index}.txt`
    # Extract that info and read the file to get the duration and the text
    # in order to create VOLine objects
    for file in files:
        scene_index, line_index, sentence_index = [
            int(i) for i in re.findall(r"\d+", file)
        ]
        with open(os.path.join(utils.VOICEOVER_PATH, file), "r") as f:
            text = f.read()
        vo_file_json = json.loads(text)
        vo_lines.append(
            VOLine(
                actor=None,
                line=vo_file_json["sentence"],
                duration=vo_file_json["duration"],
                scene_index=scene_index,
                line_index=line_index,
                sentence_index=sentence_index,
            )
        )
    # Sort the lines by scene index, line index and sentence index
    vo_lines.sort(key=lambda x: (x.scene_index, x.line_index, x.sentence_index))
    return vo_lines


def get_script():
    """Retrieve the script from the script file."""
    with open(utils.SCRIPT, "r") as file:
        return yaml.load(file.read(), Loader=yaml.Loader)


def get_scenes():
    """Retrieve the scenes from the script file."""
    script = get_script()
    scenes = []
    for scene in script:
        characters_in_script = {}
        for character in scene["characters"]:
            characters_in_script[character["name"]] = Actor.from_name(
                character["actor"].strip().lower()
            )

        scenes.append(
            Scene(
                scene_title=scene["title"].strip(),
                description=scene["description"].strip(),
                start_time=None,
                duration=None,
                characters=characters_in_script,
                dialogue=[
                    SceneDialogue(
                        actor=characters_in_script[dialogue["character"]],
                        character_name=dialogue["character"],
                        line=dialogue["content"],
                    )
                    for dialogue in scene["dialogue"]
                ],
            )
        )

    # Check if timecodes are available
    if not os.path.exists(utils.VOICEOVER_TIMECODES):
        return scenes
    timecodes = [
        float(t)
        for t in open(utils.VOICEOVER_TIMECODES, "r").readlines()
        if t.strip() != ""
    ]
    # Calculate duration of each scene
    for i, scene in enumerate(scenes):
        if i == len(scenes) - 1:
            scene.duration = get_voiceover_duration() - timecodes[i]
        else:
            scene.duration = timecodes[i + 1] - timecodes[i]
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
    else:
        logger.warning(f"Unknown param: {param_name}")
        return ""
