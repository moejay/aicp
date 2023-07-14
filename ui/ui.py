from utils import utils
from models import Director, ProductionConfig
from ui.actor_creator import actor_creator_ui
from ui.director_creator import director_creator_ui
import gradio as gr
import os


# List files in the actors directory
# Filter by yaml files, and remove the extension
actors = [f.split(".")[0] for f in os.listdir(utils.ACTOR_PATH) if f.endswith(".yaml")]
# Same for directors
directors = [
    f.split(".")[0] for f in os.listdir(utils.DIRECTOR_PATH) if f.endswith(".yaml")
]
# Same for configs
production_configs = [
    f.split(".")[0]
    for f in os.listdir(utils.PRODUCTION_CONFIG_PATH)
    if f.endswith(".yaml")
]
# Same for programs
programs = [
    f.split(".")[0]
    for f in os.listdir(utils.PROGRAMS_PATH_PREFIX)
    if f.endswith(".yaml")
]

current_config = ProductionConfig.from_yaml(
    os.path.join(utils.PRODUCTION_CONFIG_PATH, f"{production_configs[0]}.yaml")
)


def change_director(director):
    """Change the current director"""
    d = Director.from_yaml(os.path.join(utils.DIRECTOR_PATH, f"{director}.yaml"))
    return "\n".join([f"{k}: {v}" for k, v in d.as_dict().items()])


def change_config(config):
    """Change the current config"""
    c = ProductionConfig.from_yaml(
        os.path.join(utils.PRODUCTION_CONFIG_PATH, f"{config}.yaml")
    )
    return "\n".join([f"{k}: {v}" for k, v in c.__dict__.items()])


def make_ui(prep_video_params):
    with gr.Blocks() as demo:
        with gr.Tab("Make a video"):
            video_prompt = gr.Textbox(lines=1, label="Video Prompt", value="Your Mom")
            working_dir = gr.Textbox(label="Working Directory", value="output")
            step = gr.Dropdown(
                label="Start At",
                choices=[
                    "Researcher",
                    "Script Writer",
                    "Storyboard Artist",
                    "Voiceover Artist",
                    "Music Composer",
                    "Sound Engineer",
                    "Producer",
                    "Thumbnail Artist",
                    "Youtube Distributor",
                ],
                value="Researcher",
            )
            single_step = gr.Checkbox(label="Single Step", value=False)
            submit = gr.Button(label="Submit")

            with gr.Accordion("Configure stuff"):
                with gr.Tab("Program"):
                    program = gr.Dropdown(
                        label="Programs",
                        choices=programs,
                        value=programs[0],
                        interactive=True,
                    )

                with gr.Tab("Actors"):
                    actor = gr.CheckboxGroup(
                        label="Actors",
                        choices=actors,
                        value=[actors[0]],
                        interactive=True,
                    )
                with gr.Tab("Director"):
                    director = gr.Dropdown(
                        label="Directors",
                        choices=directors,
                        value=directors[0],
                        interactive=True,
                    )
                    director_cast = gr.Textbox(
                        label="Director Cast", value=change_director(directors[0])
                    )
                    director.change(
                        fn=change_director, inputs=director, outputs=director_cast
                    )
                with gr.Tab("Production Config"):
                    production_config = gr.Dropdown(
                        label="Production Configs",
                        choices=production_configs,
                        value=production_configs[0],
                        interactive=True,
                    )
                    production_config_contents = gr.Textbox(
                        label="Production Config Contents",
                        value=change_config(production_configs[0]),
                    )
                    production_config.change(
                        fn=change_config,
                        inputs=production_config,
                        outputs=production_config_contents,
                    )
            output = gr.Textbox(label="Output", value="")
            submit.click(
                prep_video_params,
                inputs=[
                    video_prompt,
                    program,
                    director,
                    actor,
                    production_config,
                    working_dir,
                    step,
                    single_step,
                ],
                outputs=output,
            )
        with gr.Tab("Create an Actor"):
            actor_creator_ui()
        with gr.Tab("Create a Director"):
            director_creator_ui()

    return demo
