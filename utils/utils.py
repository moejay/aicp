# Description: Utility functions for the project.
import os

# Those are the creation paths (files that get created during a run)
PATH_PREFIX = ""
RESEARCH = "research.yaml"
SCRIPT = "script.yaml"
STORYBOARD_PATH = "storyboard"
THUMBNAILS_PATH = "thumbnails"
VOICEOVER_WAV_FILE = "script.wav"
FINAL_AUDIO_FILE = "audio.wav"
VOICEOVER_TIMECODES = "voiceover_timecodes.txt"
TEMP_VIDEO_FILE = "temp_video.mp4"
FINAL_VIDEO_FILE = "video.mp4"
MUSIC_PATH = "music"
DISTRIBUTION_METADATA_FILE = "distribution_metadata.yaml"

# Those are production paths (files that are used to start a run)
CAST_PATH_PREFIX = os.environ.get("CAST_PATH_PREFIX", "cast")
ACTOR_PATH = os.path.join(CAST_PATH_PREFIX, "actors")
SPEAKER_PATH = "speakers"
DIRECTOR_PATH = os.path.join(CAST_PATH_PREFIX, "directors")
RESEARCHER_PATH = os.path.join(CAST_PATH_PREFIX, "researchers")
SCRIPT_WRITER_PATH = os.path.join(CAST_PATH_PREFIX, "script_writers")
STORYBOARD_ARTIST_PATH = os.path.join(CAST_PATH_PREFIX, "storyboard_artists")
THUMBNAIL_ARTIST_PATH = os.path.join(CAST_PATH_PREFIX, "thumbnail_artists")
VOICEOVER_ARTIST_PATH = os.path.join(CAST_PATH_PREFIX, "voiceover_artists")
MUSIC_COMPOSER_PATH = os.path.join(CAST_PATH_PREFIX, "music_composers")
YOUTUBE_DISTRIBUTOR_PATH = os.path.join(CAST_PATH_PREFIX, "youtube_distributors")
PRODUCTION_CONFIG_PATH = os.path.join(CAST_PATH_PREFIX, "production_configs")

PROGRAMS_PATH_PREFIX = os.environ.get("PROGRAMS_PATH_PREFIX", "programs")
programs = [
    f.split(".")[0] for f in os.listdir(PROGRAMS_PATH_PREFIX) if f.endswith(".yaml")
]

researchers = [
    f.split(".")[0] for f in os.listdir(RESEARCHER_PATH) if f.endswith(".yaml")
]
script_writers = [
    f.split(".")[0] for f in os.listdir(SCRIPT_WRITER_PATH) if f.endswith(".yaml")
]
storyboard_artists = [
    f.split(".")[0] for f in os.listdir(STORYBOARD_ARTIST_PATH) if f.endswith(".yaml")
]
thumbnail_artists = [
    f.split(".")[0] for f in os.listdir(THUMBNAIL_ARTIST_PATH) if f.endswith(".yaml")
]
voiceover_artists = [
    f.split(".")[0] for f in os.listdir(VOICEOVER_ARTIST_PATH) if f.endswith(".yaml")
]
music_composers = [
    f.split(".")[0] for f in os.listdir(MUSIC_COMPOSER_PATH) if f.endswith(".yaml")
]
youtube_distributors = [
    f.split(".")[0] for f in os.listdir(YOUTUBE_DISTRIBUTOR_PATH) if f.endswith(".yaml")
]
production_configs = [
    f.split(".")[0] for f in os.listdir(PRODUCTION_CONFIG_PATH) if f.endswith(".yaml")
]


def set_prefix(prefix):
    """Set the prefix of the project."""
    global PATH_PREFIX, RESEARCH, SCRIPT, STORYBOARD_PATH, VOICEOVER_WAV_FILE, FINAL_AUDIO_FILE, VOICEOVER_TIMECODES, TEMP_VIDEO_FILE, FINAL_VIDEO_FILE, MUSIC_PATH, DISTRIBUTION_METADATA_FILE, THUMBNAILS_PATH

    PATH_PREFIX = prefix
    RESEARCH = os.path.join(prefix, RESEARCH.split("/")[-1])
    SCRIPT = os.path.join(prefix, SCRIPT.split("/")[-1])
    VOICEOVER_WAV_FILE = os.path.join(prefix, VOICEOVER_WAV_FILE.split("/")[-1])
    FINAL_AUDIO_FILE = os.path.join(prefix, FINAL_AUDIO_FILE.split("/")[-1])
    VOICEOVER_TIMECODES = os.path.join(prefix, VOICEOVER_TIMECODES.split("/")[-1])
    FINAL_VIDEO_FILE = os.path.join(prefix, FINAL_VIDEO_FILE.split("/")[-1])
    TEMP_VIDEO_FILE = os.path.join(prefix, TEMP_VIDEO_FILE.split("/")[-1])
    DISTRIBUTION_METADATA_FILE = os.path.join(
        prefix, DISTRIBUTION_METADATA_FILE.split("/")[-1]
    )

    STORYBOARD_PATH = os.path.join(prefix, STORYBOARD_PATH.split("/")[-1])
    os.makedirs(STORYBOARD_PATH, exist_ok=True)

    THUMBNAILS_PATH = os.path.join(prefix, THUMBNAILS_PATH.split("/")[-1])
    os.makedirs(THUMBNAILS_PATH, exist_ok=True)

    MUSIC_PATH = os.path.join(prefix, MUSIC_PATH.split("/")[-1])
    os.makedirs(MUSIC_PATH, exist_ok=True)
