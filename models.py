from __future__ import annotations
from pydantic import BaseModel
from abc import ABC, abstractmethod

class AICPMetadata(BaseModel):
    """Class encapsulating the metadata for an AICP video."""

    title: str
    description: str | None

class Processable(BaseModel, ABC):
    """Class encapsulating the processable for an AICP video."""
    id: str
    duration: float | None

    @abstractmethod
    def process(self):
        pass

class AICPLayer(Processable):
    """Class encapsulating the layer for an AICP video."""
    
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

class AICPClip(Processable):
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

class AICPVideo(BaseModel):
    """Class encapsulating the video for an AICP video."""

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

class AICPScript(BaseModel):
    """Class encapsulating the script for an AICP video."""
    


class AICPProgram(BaseModel):
    """Class encapsulating the program for an AICP video."""
    name: str
    description: str
    prompt_placeholder_text: str
    script_rules: str | None
    storyboards: str | None

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
    name: str
    description: str | None
    program: AICPProgram
    production_config: AICPProductionConfig


