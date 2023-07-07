import os

import contextlib
import wave
import json
import yaml

from models import Scene

from utils import utils


def get_voiceover_duration():
    """Get the duration of the voiceover script."""
    with contextlib.closing(wave.open(utils.VOICEOVER_WAV_FILE, "r")) as f:
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
                scene_title=scene["title"].strip(),
                description=scene["description"].strip(),
                content=scene["narrator"].strip(),
                start_time=None,
                duration=None,
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
        if i == len(timecodes) - 1:
            scene.duration = get_voiceover_duration() - timecodes[i]
        else:
            scene.duration = timecodes[i + 1] - timecodes[i]
        scene.start_time = timecodes[i]

    return scenes
