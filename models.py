from pydantic import BaseModel

class AICPMetadata(BaseModel):
    """Class encapsulating the metadata for an AICP video."""

    title: str
    description: str | None
    program: str
    original_prompt: str | None
    research_result: str | None

class AICPLayer(BaseModel):
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

class AICPClip(BaseModel):
    """Class encapsulating the clip for an AICP video."""
    id: str
    layers: list[AICPLayer]

class AICPShot(AICPClip):
    """Class encapsulating the shot for an AICP video."""
    pass

class AICPScene(AICPClip):
    """Class encapsulating the scene for an AICP video."""
    shots: list[AICPShot]

class AICPSequence(AICPClip):
    """Class encapsulating the sequence for an AICP video."""
    scenes: list[AICPScene]

class AICPOutline(BaseModel):
    """Class encapsulating the outline for an AICP video."""
    sequences: list[AICPSequence]

class AICPVideo(BaseModel):
    """Class encapsulating the video for an AICP video."""
    metadata: AICPMetadata | None
    outline: AICPOutline | None
