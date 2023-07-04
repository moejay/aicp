import gradio as gr
import os
import logging
from typing import Optional

from utils import utils
from aicp import make_video
from models import Director
from argparse import ArgumentParser
from ui.ui import make_ui

logger = logging.getLogger(__name__)

def prep_video_params(prompt, director, actors, working_dir, step):
    """ Prepare the video parameters for the make_video function """
    director = Director.from_yaml(os.path.join(utils.DIRECTOR_PATH, director + ".yaml"))
    return make_video(prompt, director, actors, working_dir, step)

parser = ArgumentParser()
parser.add_argument("--ui", action="store_true", help="Launch the UI")
parser.add_argument("--prompt", help="The prompt to use for the video")
parser.add_argument("--director", help="The director to use for the video")
parser.add_argument("--actors", nargs="+", help="The actors to use for the video")
parser.add_argument("--output", help="The output directory to write to")


if __name__ == "__main__":
    args = parser.parse_args()
    if args.ui:
        # Launch the UI
        app = make_ui(prep_video_params)
        app.launch(server_name="0.0.0.0")

    elif args.prompt and args.director and args.actors:
        # Make the video
        retries = 3
        while retries > 0:
            try:
                result = prep_video_params(args.prompt, args.director, args.actors, args.output, "Researcher")
                print(result)
                break
            except Exception as e:
                logger.exception(e)
                retries -= 1
                print(f"Failed to make video, {retries} retries left")
    else:
        # Print help
        parser.print_help()

