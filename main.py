import gradio as gr
import os
import logging

from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType

from tools.music_composer import MusicComposerTool
from tools.producer import ProducerTool
from tools.researcher import ResearcherTool
from tools.script_writer import ScriptWriterTool
from tools.sound_engineer import SoundEngineerTool 
from tools.storyboard_artist import StoryBoardArtistTool 
from tools.thumbnail_artist import ThumbnailArtistTool
from tools.visualeffects_artist import VisualEffectsArtistTool
from tools.voiceover_artist import VoiceOverArtistTool
from tools.youtube_distributor import YoutubeDistributorTool

from utils import utils
from utils.utils import ProgramConfig
from dataclasses import dataclass

logger = logging.getLogger(__name__)


all_tools = [
    ResearcherTool(),
    ScriptWriterTool(),
    #VisualEffectsArtistTool(),
    VoiceOverArtistTool(),
    StoryBoardArtistTool(),
    MusicComposerTool(),
    SoundEngineerTool(),
    ProducerTool(),
    ThumbnailArtistTool(),
    YoutubeDistributorTool(),
]

def make_video(prompt, actor, working_dir, step):
    os.makedirs(working_dir, exist_ok=True)
    utils.set_prefix(working_dir)
    load_dotenv()

    config = ProgramConfig(
        prompt=prompt,
        actor=actor)

    
    # create tools only from step onwards
    tools = []
    starting_tool_idx = -1
    for tool_idx, tool in enumerate(all_tools):
        if tool.name == step.lower().replace(" ", ""):
            starting_tool_idx = tool_idx
            tools.append(tool)
        elif len(tools) > 0:
            tools.append(tool)

    logger.info("Starting at tool %s", tools[0].name)
    for t in tools:
        t.set_config(config)
        t.run(prompt)
    return utils.FINAL_VIDEO_FILE

# List files in the actors directory
# Filter by yaml files, and remove the extension
actors = [f.split(".")[0] for f in os.listdir(utils.ACTOR_PATH) if f.endswith(".yaml")]


with gr.Blocks() as app:
    video_prompt = gr.Textbox(lines=1, label="Video Prompt", value="Your Mom")
    actor = gr.Dropdown(label="Actor", choices=actors, value=actors[0], interactive=True)
    working_dir = gr.Textbox(label="Working Directory", value="output")
    ## Ask the user which step to start at
    step = gr.Dropdown(label="Start At", choices=[t.name for t in all_tools], value=all_tools[0].name, interactive=True)

    output = gr.Video(label="Your Video", format="mp4")

    submit = gr.Button(label="Submit")
    submit.click(make_video, inputs=[video_prompt,actor, working_dir, step], outputs=output)

app.launch(share=True)
