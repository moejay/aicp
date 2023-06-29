import gradio as gr
import os
import logging

from utils import utils
from aicp import make_video
from models import Director
logger = logging.getLogger(__name__)


# List files in the actors directory
# Filter by yaml files, and remove the extension
actors = [f.split(".")[0] for f in os.listdir(utils.ACTOR_PATH) if f.endswith(".yaml")]
# Same for directors
directors = [f.split(".")[0] for f in os.listdir(utils.DIRECTOR_PATH) if f.endswith(".yaml")]

def prep_video_params(prompt, director, actors, working_dir, step):
    """ Prepare the video parameters for the make_video function """
    director = Director.from_yaml(os.path.join(utils.DIRECTOR_PATH, director + ".yaml"))
    return make_video(prompt, director, actors, working_dir, step)

with gr.Blocks() as app:
    video_prompt = gr.Textbox(lines=1, label="Video Prompt", value="Your Mom")
    working_dir = gr.Textbox(label="Working Directory", value="output")
    actor = gr.CheckboxGroup(label="Actors", choices=actors, value=[actors[0]], interactive=True)
    # This is used to load preset
    director = gr.Dropdown(label="Directors", choices=directors, value=directors[0], interactive=True)
    with gr.Accordion("Director Config"):
        with gr.Tab("Researcher"):
            researcher = gr.Dropdown(label="Researcher", choices=utils.researchers, value=utils.researchers[0], interactive=True)
            #researcher.change(fn=change_researcher, inputs=researcher, outputs=text)
        with gr.Tab("Script Writer"):
            script_writer = gr.Dropdown(label="Script Writer", choices=utils.script_writers, value=utils.script_writers[0], interactive=True)
        with gr.Tab("Storyboard Artist"):
            storyboard_artist = gr.Dropdown(label="Storyboard Artist", choices=utils.storyboard_artists, value=utils.storyboard_artists[0], interactive=True)
        with gr.Tab("Thumbnail Artist"):
            thumbnail_artist = gr.Dropdown(label="Thumbnail Artist", choices=utils.thumbnail_artists, value=utils.thumbnail_artists[0], interactive=True)
        with gr.Tab("Voiceover Artist"):
            voiceover_artist = gr.Dropdown(label="Voiceover Artist", choices=utils.voiceover_artists, value=utils.voiceover_artists[0], interactive=True)
        with gr.Tab("Music Composer"):
            music_composer = gr.Dropdown(label="Music Composer", choices=utils.music_composers, value=utils.music_composers[0], interactive=True)
        with gr.Tab("Youtube Distributor"):
            youtube_distributor = gr.Dropdown(label="Youtube Distributor", choices=utils.youtube_distributors, value=utils.youtube_distributors[0], interactive=True)


    ## Ask the user which step to start at
    step = gr.Dropdown(label="Start At", choices=["Researcher", "Script Writer", "Storyboard Artist", "Voiceover Artist", "Music Composer", "Sound Engineer", "Producer", "Thumbnail Artist" , "Youtube Distributor" ])

    output = gr.Video(label="Your Video", format="mp4")

    submit = gr.Button(label="Submit")
    submit.click(prep_video_params, inputs=[video_prompt, director, actor, working_dir, step], outputs=output)

app.launch()
