import gradio as gr
import os

from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType

from tools.music_conductor import MusicConductorTool
from tools.producer import ProducerTool
from tools.researcher import ResearcherTool
from tools.script_writer import ScriptWriterTool
from tools.sound_engineer import SoundEngineerTool 
from tools.storyboard_artist import StoryBoardArtistTool 
from tools.voiceover_artist import VoiceOverArtistTool

from utils import utils


def make_video(prompt, working_dir):
    os.makedirs(working_dir, exist_ok=True)
    utils.set_prefix(working_dir)
    load_dotenv()

    tools = [
        MusicConductorTool(),
        ProducerTool(),
        ResearcherTool(),
        ScriptWriterTool(),
        SoundEngineerTool()
        StoryBoardArtistTool(),
        VisualEffectsArtistTool(),
        VoiceOverArtistTool(),
        ]

    llm = ChatOpenAI(temperature=0, streaming=True)
    mrkl = initialize_agent(tools, llm, agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

    mrkl.run(f"""
    1. Research {prompt} using researcher tool.
    2. Write a script using the scriptwriter tool.
    3. Generate images using the storyboardartist tool.
    4. Generate audio using the speechgenerator tool.
    5. Generate the music using the musicconductor tool.
    6. Finalize the audio using the soundengineer tool.
    7. Produce the video using the producer tool.
            """)
    return utils.FINAL_VIDEO_FILE


with gr.Blocks() as app:
    video_prompt = gr.Textbox(lines=1, label="Video Prompt", value="Your Mom")
    working_dir = gr.Textbox(label="Working Directory", value="output")
    output = gr.Video(label="Your Video")
    submit = gr.Button(label="Submit")
    submit.click(make_video, inputs=[video_prompt, working_dir], outputs=output)

app.launch()
