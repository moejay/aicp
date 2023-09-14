from __future__ import annotations
from pydantic import BaseModel


class AICPMetadata(BaseModel):
    """Class encapsulating the metadata for an AICP video."""

    title: str
    description: str | None


class AICPLayer(BaseModel):
    """Class encapsulating the layer for an AICP video."""

    id: str
    duration: float | None = None


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
    prompt: str
    positive_prompt: str
    negative_prompt: str
    model: str
    seed: int
    width: int
    height: int


class AICPClip(BaseModel):
    """Class encapsulating the clip for an AICP video."""

    id: str
    layers: list[AICPVideoLayer|AICPVoiceoverLayer|AICPMusicLayer] = []
    # transitions: list[AICPTransition]

    def get_layer_by_id(self, id: str) -> AICPLayer | None:
        """Returns the layer with the given id."""
        for layer in self.layers:
            if layer.id == id:
                return layer
        return None


class AICPShot(AICPClip):
    """Class encapsulating the shot for an AICP video."""
    title: str
    description: str
    artistic_direction: str
    dialog_line: str | None = None
    dialog_character: str | None = None


class AICPScene(AICPClip):
    """Class encapsulating the scene for an AICP video."""

    shots: list[AICPShot] = []
    summary: str | None = None

    def get_shot_by_id(self, id: str) -> AICPShot | None:
        """Returns the shot with the given id."""
        for shot in self.shots:
            if shot.id == id:
                return shot
        return None

class AICPSequence(AICPClip):
    """Class encapsulating the sequence for an AICP video."""

    scenes: list[AICPScene] = []
    summary: str | None

    def get_scene_by_id(self, id: str) -> AICPScene | None:
        """Returns the scene with the given id."""
        for scene in self.scenes:
            if scene.id == id:
                return scene
        return None


class AICPOutline(AICPClip):
    """Class encapsulating the outline for an AICP video."""

    sequences: list[AICPSequence] = []

    def get_sequence_by_id(self, id: str) -> AICPSequence | None:
        """Returns the sequence with the given id."""
        for sequence in self.sequences:
            if sequence.id == id:
                return sequence
        return None


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

    def get_all_characters(self):
        """Returns a list of all characters in the script."""
        characters = set()
        for sequence in self.sequences:
            for scene in sequence.scenes:
                for line in scene.lines:
                    characters.add(line.character)
        return characters


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
    voiceline_synced_storyboard: bool = (
        False  # Will be at some point replaced creatively by the AI
    )
    num_images_per_scene: int = 1  # Will be at some point replaced creatively by the AI


class AICPProject(BaseModel):
    """Class encapsulating the project for an AICP video."""

    id: str
    name: str
    description: str | None = None
    program: AICPProgram
    production_config: AICPProductionConfig
    actors: list[AICPActor] = []
    seed: int


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


class AICPStoryboardArtist(BaseModel):
    """Class encapsulating the storyboard artist for an AICP video."""

    name: str
    sd_model: str
    positive_prompt: str
    negative_prompt: str

   