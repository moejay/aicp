import os
import logging
from dotenv import load_dotenv
from utils import utils
from models import Director, ProductionConfig

from tools.music_composer import MusicComposerTool
from tools.producer import ProducerTool
from tools.researcher import ResearcherTool
from tools.script_writer import ScriptWriterTool
from tools.sound_engineer import SoundEngineerTool
from tools.storyboard_artist import StoryBoardArtistTool
from tools.thumbnail_artist import ThumbnailArtistTool
from tools.voiceover_artist import VoiceOverArtistTool
from tools.youtube_distributor import YoutubeDistributorTool

logger = logging.getLogger(__name__)


def make_video(
    prompt: str,
    director: Director,
    actors: list[str],
    config: ProductionConfig,
    working_dir: str,
    step: str,
):
    os.makedirs(working_dir, exist_ok=True)
    utils.set_prefix(working_dir)
    load_dotenv()

    all_tools = [
        ResearcherTool(),
        ScriptWriterTool(),
        StoryBoardArtistTool(),
        VoiceOverArtistTool(),
        MusicComposerTool(),
        SoundEngineerTool(),
        ProducerTool(),
        ThumbnailArtistTool(),
        YoutubeDistributorTool(),
    ]

    # create tools only from step onwards
    tools = []
    for _, tool in enumerate(all_tools):
        if tool.name == step.lower().replace(" ", ""):
            tools.append(tool)
        elif len(tools) > 0:
            tools.append(tool)

    logger.info("Starting at tool %s", tools[0].name)
    for t in tools:
        t.set_config(director=director, actors=actors, config=config)
        t.run(prompt)
    return utils.FINAL_VIDEO_FILE
