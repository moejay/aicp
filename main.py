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
from tools.visualeffects_artist import VisualEffectsArtistTool
from tools.voiceover_artist import VoiceOverArtistTool
from tools.youtube_distributor import YoutubeDistributorTool

from utils import utils

logger = logging.getLogger(__name__)


def make_video(prompt, working_dir, step):
    os.makedirs(working_dir, exist_ok=True)
    utils.set_prefix(working_dir)
    load_dotenv()

    all_tools = [
        ResearcherTool(),
        ScriptWriterTool(),
        StoryBoardArtistTool(),
        #VisualEffectsArtistTool(),
        VoiceOverArtistTool(),
        MusicComposerTool(),
        SoundEngineerTool(),
        ProducerTool(),
        YoutubeDistributorTool(),
    ] 
    
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
    llm = ChatOpenAI(temperature=0, streaming=True)
    mrkl = initialize_agent(tools, llm, agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

    task_list = [
     "Research {prompt} using researcher tool.",
     "Write a script using the scriptwriter tool.",
     "Generate images using the storyboardartist tool.",
     "Generate audio using the voiceoverartist tool.",
     "Generate the music using the musiccomposer tool.",
     "Finalize the audio using the soundengineer tool.",
     "Produce the video using the producer tool.",
     "Distribute the produced video using the youtubedistributor tool.",
            ]
    # Add the prompts as a numbered task list
    # based on the step the user chose
    final_tasks = ""
    for i, task in enumerate(task_list):
        if i < starting_tool_idx:
            continue
        final_tasks += f"{i+1}. {task}\n"

    mrkl.run(final_tasks.format(prompt=prompt))
    return utils.FINAL_VIDEO_FILE


with gr.Blocks() as app:
    video_prompt = gr.Textbox(lines=1, label="Video Prompt", value="Your Mom")
    working_dir = gr.Textbox(label="Working Directory", value="output")
    ## Ask the user which step to start at
    step = gr.Dropdown(label="Start At", choices=["Researcher", "Script Writer", "Storyboard Artist", "Voiceover Artist", "Music Composer", "Sound Engineer", "Producer", "Youtube Distributor" ])

    output = gr.Video(label="Your Video", format="mp4")

    submit = gr.Button(label="Submit")
    submit.click(make_video, inputs=[video_prompt, working_dir, step], outputs=output)

app.launch(share=True)
