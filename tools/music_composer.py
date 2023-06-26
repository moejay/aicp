import json
import os
import subprocess

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool
from typing import Optional, Type
from langchain import OpenAI
from utils.utils import get_scenes, get_script
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write
from pydub import AudioSegment
from utils import utils

class MusicComposerTool(BaseTool):
    name = "musiccomposer"
    description = "Useful when you need to generate a music score for the script"

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""

        llm = OpenAI(temperature=0.5)
        response = llm(f"""
            Given the following script,
            your task is to analyze the general mood of the script and create appropriate 
            background music for it.
            You should generate one description per scene in the script.

            Respond in the following format (JSON array) and one prompt per scene.

            [
                "Upbeat rock guitar solo, with modern electronic music elements",
                "Slow classical cello playing with city scape background",
                ...
            ]


            Here is the script, make sure you respond in valid JSON, and only respond with the music descriptions:
            {get_script()}
        """)

        try:
            music_prompts = json.loads(response)
        except:
            return "Please try again, invalid response"

        scenes = get_scenes()
        if len(music_prompts) < len(scenes):
            return "Please try again, not enough music prompts"
        model = MusicGen.get_pretrained("medium")
        for i, ( scene, mp ) in enumerate(zip(scenes, music_prompts)):
            print(f"SCENE: {scene}")
            model.set_generation_params(
                        use_sampling=True,
                        top_k=250,
                        duration=min(30, scene.duration)
                    )
            output = model.generate(
                        descriptions=[mp],
                        progress=True,
                    )
            filename = os.path.join(utils.MUSIC_PATH, f"music-{i}.wav")
            audio_write(
                        filename,
                        output[0].to("cpu"), 
                        model.sample_rate,
                        strategy="rms",
                        rms_headroom_db=16,
                        add_suffix=False
                    )

        return "Done generating music score"


    def _arun(self, query:str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        raise NotImplementedError("Async version of this tool is not implemented")
