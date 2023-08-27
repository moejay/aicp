import os
import logging

from argparse import ArgumentParser
from ui.ui import make_ui

logging.basicConfig(
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)

parser = ArgumentParser()
parser.add_argument("--ui", action="store_true", help="Launch the UI")
parser.add_argument("--prompt", help="The prompt to use for the video")
parser.add_argument("--director", help="The director to use for the video")
parser.add_argument(
    "--production-config", help="The production config to use for the video"
)
parser.add_argument("--actors", nargs="+", help="The actors to use for the video")
parser.add_argument("--program", help="The program aka show to use for the video")
parser.add_argument("--output", help="The output directory to write to")
parser.add_argument("--step", help="The step to start at", default="Researcher")
parser.add_argument("--single-step", action="store_true", help="Run a single step")


demo = make_ui()

if __name__ == "__main__":
    args = parser.parse_args()
    if args.ui:
        # Launch the UI
        demo.launch(server_name="0.0.0.0")

    elif args.prompt and args.director and args.actors:
        # Make the video
        retries = 3
        while retries > 0:
            try:
                print(
                    f"""Making video with 
                prompt: {args.prompt}
                program: {args.program}
                director: {args.director}
                actors: {args.actors}
                production config: {args.production_config}
                output: {args.output}
                """
                )
                break
            except Exception as e:
                logger.exception(e)
                retries -= 1
                print(f"Failed to make video, {retries} retries left")
    else:
        # Print help
        parser.print_help()
