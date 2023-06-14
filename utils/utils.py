# Description: Utility functions for the project.

from dataclasses import dataclass
import os
import contextlib
import wave
from typing import Optional

RESEARCH = 'research.txt'
SCRIPT = 'script.txt'
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

def get_voiceover_duration():
    """Get the duration of the voiceover script."""
    with contextlib.closing(wave.open(VOICEOVER_WAV_FILE,'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
    return int(duration)

def get_script():
    """Retrieve the script from the script file."""
    return open(SCRIPT, "r").read()

def get_scenes():
    """Retrieve the scenes from the script file.
       if available, use the time codes to add scene information.
       Scenes files format:
       [Scene n: title] - Description

       NARRATOR: Content


    """
    lines = open(SCRIPT, "r").readlines()
    scenes = []
    for line in lines:
        if line.startswith("[Scene"):
            scene_title, description = line.split("]")
            scenes.append(
                    Scene(
                        scene_title=scene_title.strip(),
                        description=description.strip(),
                        content="",
                        start_time=None,
                        duration=None
                    )
                    )
        elif line.strip() != "":
            scenes[-1].content += f"{line}\n"

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
