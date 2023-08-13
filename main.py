import os
import logging

from utils import utils
from aicp import make_video
from models import Director, ProductionConfig, Video, Program, Actor
from argparse import ArgumentParser
from ui.ui import make_ui

logging.basicConfig(
        level=logging.DEBUG,
)


def prep_video_params(
    prompt,
    program: str,
    director: str,
    actors: str,
    config: str,
    working_dir,
    step: str,
    single_step: bool,
):
    """Prepare the video parameters for the make_video function"""
    video = Video(
        prompt=prompt,
        director=Director.from_yaml(
            os.path.join(utils.DIRECTOR_PATH, director + ".yaml")
        ),
        actors=[Actor.from_name(actor) for actor in actors],
        production_config=ProductionConfig.from_yaml(
            os.path.join(utils.PRODUCTION_CONFIG_PATH, config + ".yaml")
        ),
        program=Program.from_yaml(
            os.path.join(utils.PROGRAMS_PATH_PREFIX, program + ".yaml")
        ),
        output_dir=working_dir,
    )
    return make_video(video, step, single_step)


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


demo = make_ui(prep_video_params)

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
                result = prep_video_params(
                    args.prompt,
                    args.program,
                    args.director,
                    args.actors,
                    args.production_config,
                    args.output,
                    args.step,
                    args.single_step,
                )
                print(result)
                break
            except Exception as e:
                logger.exception(e)
                retries -= 1
                print(f"Failed to make video, {retries} retries left")
    else:
        # Print help
        parser.print_help()
