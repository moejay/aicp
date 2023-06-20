# Description: Utility functions for the project.

from dataclasses import dataclass
from typing import Optional

import os
import contextlib
import wave
import yaml



RESEARCH = 'research.yaml'
SCRIPT = 'script.yaml'
VOICEOVER_WAV_FILE = 'script.wav'
FINAL_AUDIO_FILE = 'audio.wav'
VOICEOVER_TIMECODES = 'script_timecodes.txt'
FINAL_VIDEO_FILE = 'video.mp4'


@dataclass
class Scene:
    """A scene object."""
    start_time: Optional[float] # The scene starting
    duration: Optional[float] # The duration of the scene in seconds
    scene_title: str # The title of the scene
    description: str # The description of the scene
    content: str # The content of the scene

def set_prefix(prefix):
    """Set the prefix of the project."""
    global RESEARCH, SCRIPT, VOICEOVER_WAV_FILE, FINAL_AUDIO_FILE, VOICEOVER_TIMECODES, FINAL_VIDEO_FILE
    RESEARCH = os.path.join(prefix, RESEARCH.split('/')[-1])
    SCRIPT = os.path.join(prefix, SCRIPT.split('/')[-1])
    VOICEOVER_WAV_FILE = os.path.join(prefix, VOICEOVER_WAV_FILE.split('/')[-1] )
    FINAL_AUDIO_FILE = os.path.join(prefix, FINAL_AUDIO_FILE.split('/')[-1])
    VOICEOVER_TIMECODES = os.path.join(prefix, VOICEOVER_TIMECODES.split('/')[-1] )
    FINAL_VIDEO_FILE = os.path.join(prefix, FINAL_VIDEO_FILE.split('/')[-1])

def get_voiceover_duration():
    """Get the duration of the voiceover script."""
    with contextlib.closing(wave.open(VOICEOVER_WAV_FILE,'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
    return int(duration)

def get_script():
    """Retrieve the script from the script file."""
    with open(SCRIPT, "r") as file:
        return yaml.load(file, Loader=yaml.Loader)

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
    if not os.path.exists(VOICEOVER_TIMECODES):
        return scenes
    timecodes = [
            float(t) for t in open(VOICEOVER_TIMECODES, "r").readlines() if t.strip() != ""
            ]
    # Calculate duration of each scene
    for i, scene in enumerate(scenes):
        if i == len(timecodes) - 1:
            scene.duration = get_voiceover_duration() - timecodes[i]
        else:
            scene.duration = timecodes[i+1] - timecodes[i]
        scene.start_time = timecodes[i]

    return scenes

def get_config():
    """Retrieve the research config."""
    with open("config.yaml", "r") as file:
        return yaml.load(file, Loader=yaml.Loader)
