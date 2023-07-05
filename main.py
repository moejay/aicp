import gradio as gr
import os
import logging
from typing import Optional

from utils import utils
from aicp import make_video
from models import Director
logger = logging.getLogger(__name__)


# List files in the actors directory
# Filter by yaml files, and remove the extension
actors = [f.split(".")[0] for f in os.listdir(utils.ACTOR_PATH) if f.endswith(".yaml")]
# Same for directors
directors = [f.split(".")[0] for f in os.listdir(utils.DIRECTOR_PATH) if f.endswith(".yaml")]


current_director = Director.from_yaml(os.path.join(utils.DIRECTOR_PATH, f"{directors[0]}.yaml"))

def prep_video_params(prompt, director, actors, working_dir, step):
    """ Prepare the video parameters for the make_video function """
    director = Director.from_yaml(os.path.join(utils.DIRECTOR_PATH, director + ".yaml"))
    return make_video(prompt, director, actors, working_dir, step)

def save_director(director_file_name, researcher, script_writer, storyboard_artist, thumbnail_artist, voiceover_artist, music_composer, youtube_distributor):
    """ Save the director to a yaml file """
    director = Director(researcher, script_writer, storyboard_artist, thumbnail_artist, voiceover_artist, music_composer, youtube_distributor)
    director.to_yaml(os.path.join(utils.DIRECTOR_PATH, f"{director_file_name}.yaml" ))
    return f"Director saved to {director_file_name}.yaml"

def change_director(director):
    """ Change the current director """
    d = Director.from_yaml(os.path.join(utils.DIRECTOR_PATH, f"{director}.yaml"))
    return "\n".join([f"{k}: {v}" for k, v in d.as_dict().items()])

def change_artist(artist):
    def change(new_artist_name):
        setattr(current_director, artist, new_artist_name) 
        return getattr(current_director, f"get_{artist}")().prompt
    return change

with gr.Blocks() as app:
    with gr.Tab("Make a video"):
        video_prompt = gr.Textbox(lines=1, label="Video Prompt", value="Your Mom")
        working_dir = gr.Textbox(label="Working Directory", value="output")

        actor = gr.CheckboxGroup(label="Actors", choices=actors, value=[actors[0]], interactive=True)
        director = gr.Dropdown(label="Directors", choices=directors, value=directors[0], interactive=True)
        director_cast = gr.Textbox(label="Director Cast", value="cast here")
        director.change(fn=change_director, inputs=director, outputs=director_cast)
        ## Ask the user which step to start at
        step = gr.Dropdown(label="Start At", choices=["Researcher", "Script Writer", "Storyboard Artist", "Voiceover Artist", "Music Composer", "Sound Engineer", "Producer", "Thumbnail Artist" , "Youtube Distributor" ])

        output = gr.Video(label="Your Video", format="mp4")
        submit = gr.Button(label="Submit")
        submit.click(prep_video_params, inputs=[video_prompt, director, actor, working_dir, step], outputs=output)

    with gr.Tab("Create a Director"):
        with gr.Tab("Researcher"):
            researcher = gr.Dropdown(label="Researcher", choices=utils.researchers, value=utils.researchers[0], interactive=True)
            researcher_prompt = gr.Textbox(max_lines=10, label="Researcher Prompt", value="Your Mom")
            researcher.change(fn=change_artist("researcher") , inputs=researcher, outputs=researcher_prompt)
        with gr.Tab("Script Writer"):
            script_writer = gr.Dropdown(label="Script Writer", choices=utils.script_writers, value=utils.script_writers[0], interactive=True)
            script_writer_prompt = gr.Textbox(max_lines=10, label="Script Writer Prompt", value="Your Mom")
            script_writer.change(fn=change_artist("script_writer") , inputs=script_writer, outputs=script_writer_prompt)
        with gr.Tab("Storyboard Artist"):
            storyboard_artist = gr.Dropdown(label="Storyboard Artist", choices=utils.storyboard_artists, value=utils.storyboard_artists[0], interactive=True)
            storyboard_artist_prompt = gr.Textbox(max_lines=10, label="Storyboard Artist Prompt", value="Your Mom")
            storyboard_artist.change(fn=change_artist("storyboard_artist") , inputs=storyboard_artist, outputs=storyboard_artist_prompt)
        with gr.Tab("Thumbnail Artist"):
            thumbnail_artist = gr.Dropdown(label="Thumbnail Artist", choices=utils.thumbnail_artists, value=utils.thumbnail_artists[0], interactive=True)
            thumbnail_artist_prompt = gr.Textbox(max_lines=10, label="Thumbnail Artist Prompt", value="Your Mom")
            thumbnail_artist.change(fn=change_artist("thumbnail_artist") , inputs=thumbnail_artist, outputs=thumbnail_artist_prompt)

        with gr.Tab("Voiceover Artist"):
            voiceover_artist = gr.Dropdown(label="Voiceover Artist", choices=utils.voiceover_artists, value=utils.voiceover_artists[0], interactive=True)
            voiceover_artist_prompt = gr.Textbox(max_lines=10, label="Voiceover Artist Prompt", value="Your Mom")
            voiceover_artist.change(fn=change_artist("voiceover_artist") , inputs=voiceover_artist, outputs=voiceover_artist_prompt)

        with gr.Tab("Music Composer"):
            music_composer = gr.Dropdown(label="Music Composer", choices=utils.music_composers, value=utils.music_composers[0], interactive=True)
            music_composer_prompt = gr.Textbox(max_lines=10, label="Music Composer Prompt", value="Your Mom")
            music_composer.change(fn=change_artist("music_composer") , inputs=music_composer, outputs=music_composer_prompt)
        with gr.Tab("Youtube Distributor"):
            youtube_distributor = gr.Dropdown(label="Youtube Distributor", choices=utils.youtube_distributors, value=utils.youtube_distributors[0], interactive=True)
            youtube_distributor_prompt = gr.Textbox(max_lines=10, label="Youtube Distributor Prompt", value="Your Mom")
            youtube_distributor.change(fn=change_artist("youtube_distributor") , inputs=youtube_distributor, outputs=youtube_distributor_prompt)
        
        director_file_name = gr.Textbox(label="Director File Name", value="test")
        save_director_button = gr.Button(label="Save Director")
        save_director_result = gr.Textbox(label="Save Director Result", value="test")
        save_director_button.click(save_director, inputs=[director_file_name, researcher, script_writer, storyboard_artist, thumbnail_artist, voiceover_artist, music_composer, youtube_distributor], outputs=save_director_result)



app.launch(server_name="0.0.0.0")
