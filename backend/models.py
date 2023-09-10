from __future__ import annotations
from pydantic import BaseModel

class AICPMetadata(BaseModel):
    """Class encapsulating the metadata for an AICP video."""

    title: str
    description: str | None

class AICPLayer():
    """Class encapsulating the layer for an AICP video."""
    id: str
    duration: float | None
    
class AICPVoiceoverLayer(AICPLayer):
    """Class encapsulating the voiceover layer for an AICP video."""
    prompt: str
    speaker: str
    speaker_text_temp: float = 0.7
    speaker_waveform_temp: float = 0.7

class AICPMusicLayer(AICPLayer):
    """Class encapsulating the music layer for an AICP video."""
    prompt: str

class AICPVideoLayer(AICPLayer):
    """Class encapsulating the video layer for an AICP video."""
    positive_prompt: str
    negative_prompt: str
    model: str
    seed: int
    width: int
    height: int

class AICPClip():
    """Class encapsulating the clip for an AICP video."""
    layers: list[AICPLayer] = []
    children: list[AICPClip] = []
    # transitions: list[AICPTransition]

class AICPShot(AICPClip):
    """Class encapsulating the shot for an AICP video."""

class AICPScene(AICPClip):
    """Class encapsulating the scene for an AICP video."""

class AICPSequence(AICPClip):
    """Class encapsulating the sequence for an AICP video."""

class AICPOutline(AICPClip):
    """Class encapsulating the outline for an AICP video."""

class AICPActor(BaseModel):
    """Class encapsulating the actor for an AICP video."""
    name: str
    bio: str | None
    catch_phrase: str | None
    physical_description: str | None
    speaker: str
    speaker_text_temp: float = 0.7
    speaker_waveform_temp: float = 0.7
    

class AICPResearch(BaseModel):
    """Class encapsulating the research for an AICP video."""
    prompt: str
    result: str
    # We can other research artifacts later here

class AICPScriptLine(BaseModel):
    """Class encapsulating the script line for an AICP video."""
    character: str
    line: str
class AICPScriptScene(BaseModel):
    """Class encapsulating the script scene for an AICP video."""
    title: str
    description: str
    lines: list[AICPScriptLine] = []
class AICPScriptSequence(BaseModel):
    """Class encapsulating the script sequence for an AICP video."""
    title: str
    description: str
    scenes: list[AICPScriptScene] = []
class AICPScript(BaseModel):
    """Class encapsulating the script for an AICP video."""
    title: str
    sequences: list[AICPScriptSequence] = []

    


class AICPProgram(BaseModel):
    """Class encapsulating the program for an AICP video."""
    title: str
    description: str
    prompt_placeholder_text: str
    script_rules: str | None = None
    storyboard_rules: str | None = None
    music_rules: str | None = None

class AICPProductionConfig(BaseModel):
    """Class encapsulating the production config for an AICP video."""
    video_width: int = 1920
    video_height: int = 1080
    sd_base_image_width: int = 768
    sd_base_image_height: int = 432
    enable_subtitles: bool = False 
    voiceline_synced_storyboard: bool = False # Will be at some point replaced creatively by the AI
    num_images_per_scene: int = 1 # Will be at some point replaced creatively by the AI

class AICPProject(BaseModel):
    """Class encapsulating the project for an AICP video."""
    id: str
    name: str
    description: str | None = None
    program: AICPProgram
    production_config: AICPProductionConfig
    actors: list[AICPActor] = []


class AICPResearcher(BaseModel):
    """Class encapsulating the researcher for an AICP video."""
    name: str
    model: str
    prompt: str

class AICPScriptWriter(BaseModel):
    """Class encapsulating the scriptwriter for an AICP video."""
    name: str
    model: str
    prompt: str