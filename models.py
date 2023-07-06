import os
from pydantic.dataclasses import dataclass
from typing import Optional
from dacite import from_dict
import yaml
from utils.utils import (
        ACTOR_PATH,
        RESEARCHER_PATH,
        SCRIPT_WRITER_PATH,
        VOICEOVER_ARTIST_PATH,
        MUSIC_COMPOSER_PATH,
        STORYBOARD_ARTIST_PATH,
        THUMBNAIL_ARTIST_PATH,
        YOUTUBE_DISTRIBUTOR_PATH,
        )



@dataclass 
class CastMember:
    """An object representing a cast member."""
    name: str
    model: str
    prompt: str

@dataclass
class Researcher(CastMember):
    """An object representing a researcher."""

@dataclass
class ScriptWriter(CastMember):
    """An object representing a script writer."""

@dataclass
class StoryboardArtist(CastMember):
    """An object representing a storyboard artist."""
    positive_prompt: str
    negative_prompt: str
    sd_model: str

@dataclass
class ThumbnailArtist(CastMember):
    """An object representing a thumbnail artist."""
    positive_prompt: str
    negative_prompt: str
    sd_model: str

@dataclass
class VoiceoverArtist(CastMember):
    """An object representing a voiceover artist."""

@dataclass
class MusicComposer(CastMember):
    """An object representing a music composer."""

@dataclass
class YouTubeDistributor(CastMember):
    """An object representing a YouTube distributor."""

@dataclass
class ProductionConfig:
    """An object representing the output configuration."""
    video_width: int
    video_height: int
    sd_base_image_width: int
    sd_base_image_height: int

    @classmethod
    def from_yaml(cls, yaml_file: str):
        """Read the output configuration from a yaml file."""
        with open(yaml_file, 'r') as f:
            return from_dict(data_class=ProductionConfig, data=yaml.load(f, Loader=yaml.FullLoader))

@dataclass
class Director:
    """An object representing a director."""
    researcher: str
    script_writer: str
    storyboard_artist: str
    thumbnail_artist: str
    voiceover_artist: str
    music_composer: str
    youtube_distributor: str 

    @classmethod
    def from_yaml(cls, yaml_file: str):
        """Read the director from a yaml file."""
        with open(yaml_file, 'r') as f:
            return from_dict(data_class=Director, data=yaml.load(open(yaml_file), Loader=yaml.FullLoader))

    def to_yaml(self, yaml_file: str):
        """Write the director to a yaml file."""
        with open(yaml_file, 'w') as f:
            yaml.safe_dump(self.as_dict(), f)

    def as_dict(self):
        """Return the director as a dictionary."""
        return self.__dict__

    def get_researcher(self):
        """Get the researcher."""
        return from_dict(data_class=Researcher, data=yaml.load(open(os.path.join(RESEARCHER_PATH, f"{self.researcher}.yaml")), Loader=yaml.FullLoader))

    def get_script_writer(self):
        """Get the script writer."""
        return from_dict(data_class=ScriptWriter, data=yaml.load(open(os.path.join(SCRIPT_WRITER_PATH, f"{self.script_writer}.yaml")), Loader=yaml.FullLoader))

    def get_storyboard_artist(self):
        """Get the storyboard artist."""
        return from_dict(data_class=StoryboardArtist, data=yaml.load(open(os.path.join(STORYBOARD_ARTIST_PATH, f"{self.storyboard_artist}.yaml")), Loader=yaml.FullLoader))

    def get_thumbnail_artist(self):
        """Get the thumbnail artist."""
        return from_dict(data_class=ThumbnailArtist, data=yaml.load(open(os.path.join(THUMBNAIL_ARTIST_PATH, f"{self.thumbnail_artist}.yaml")), Loader=yaml.FullLoader))

    def get_voiceover_artist(self):
        """Get the voiceover artist."""
        return from_dict(data_class=VoiceoverArtist, data=yaml.load(open(os.path.join(VOICEOVER_ARTIST_PATH, f"{self.voiceover_artist}.yaml")), Loader=yaml.FullLoader))

    def get_music_composer(self):
        """Get the music composer."""
        return from_dict(data_class=MusicComposer, data=yaml.load(open(os.path.join(MUSIC_COMPOSER_PATH, f"{self.music_composer}.yaml")), Loader=yaml.FullLoader))

    def get_youtube_distributor(self):
        """Get the youtube distributor."""
        return from_dict(data_class=YouTubeDistributor, data=yaml.load(open(os.path.join(YOUTUBE_DISTRIBUTOR_PATH, f"{self.youtube_distributor}.yaml")), Loader=yaml.FullLoader))


@dataclass
class Scene:
    """A scene object."""
    start_time: Optional[float] # The scene starting
    duration: Optional[float] # The duration of the scene in seconds

    scene_title: str # The title of the scene
    description: str # The description of the scene
    content: str # The content of the scene

@dataclass
class Program:
    """A program aka: show"""
    title: str
    description: str

    @classmethod
    def from_yaml(cls, yaml_file: str):
        """Read the program from a yaml file."""
        with open(yaml_file, 'r') as f:
            return from_dict(data_class=Program, data=yaml.load(f, Loader=yaml.FullLoader))



@dataclass
class Actor:
    """An actor object."""
    name: str
    speaker: str
    character_bio: str

    @classmethod
    def from_yaml(cls, yaml_file: str):
        """Read the actor from a yaml file."""
        with open(yaml_file, 'r') as f:
            return from_dict(data_class=Actor, data=yaml.load(f, Loader=yaml.FullLoader))

    @classmethod
    def from_name(cls, name: str):
        """Read the actor from a name."""
        return from_dict(data_class=Actor, data=yaml.load(open(os.path.join(ACTOR_PATH, f"{name}.yaml")), Loader=yaml.FullLoader))

@dataclass
class Video:
    """Class encapsulating a video creation process."""
    prompt: str
    output_dir: str
    program: Program
    director: Director
    production_config: ProductionConfig
    actors: list[Actor]


