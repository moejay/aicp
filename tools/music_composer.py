import json
import os
import subprocess
import yaml

from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write
from langchain import LLMChain
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.prompts.chat import (ChatPromptTemplate, SystemMessagePromptTemplate, AIMessagePromptTemplate, HumanMessagePromptTemplate)
from langchain.tools import BaseTool
from pydub import AudioSegment
from typing import Optional, Type
from utils.utils import get_scenes, get_script
from utils import utils, llms
from .base import AICPBaseTool

class MusicComposerTool(AICPBaseTool):
    name = "musiccomposer"
    description = "Useful when you need to generate a music score for the script"

    scene_prompts = []

    def initialize_agent(self):
        """ Initialize the agent """
        super().initialize_agent()
        self.load_prompts()

    def load_prompts(self):
        # load voiceover artist prompts if they exist or create them 
        prompts_file = os.path.join(utils.PATH_PREFIX, "music_prompts.json")
        if os.path.exists(prompts_file):
            with open(prompts_file) as prompts:
                print("Loading existing music prompts: music_prompts.json")
                self.scene_prompts = json.loads(prompts.read().strip())
        else:
            print("Generating new music prompts...")
            self.scene_prompts = self.ego()

    def ego(self):
        template = open("prompts/music_composer.txt").read()
        chain = llms.get_llm(model=utils.get_config()["music_composer"]["ego_model"], template=template)

        script_input = yaml.dump([{ "description": s["description"]} for s in utils.get_script()])

        response = chain.run(
            script_input
        )
        print(response)

        scene_prompts = json.loads(response)
        scenes = get_scenes()

        if len(scene_prompts) < len(scenes):
            return "Please try again, not enough music prompts"

        # Save the prompts
        with open(os.path.join(utils.PATH_PREFIX, "music_prompts.json"), "w") as f:
            f.write(response)

        return scene_prompts

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        self.initialize_agent()

        model = MusicGen.get_pretrained("medium")
        scenes = get_scenes()

        for i, scene in enumerate(scenes):
            # dont recreate music, its expensive
            if os.path.exists(os.path.join(utils.MUSIC_PATH, f"music-{i+1}.wav")):
                print(f"Skipping: music-{i+1}.wav")
                continue
 
            print(f"PROMPT: {self.scene_prompts[i]['prompt']}")

            model.set_generation_params(
                        use_sampling=True,
                        top_k=250,
                        duration=min(30, scene.duration)
                    )

            output = model.generate(
                        descriptions=[self.scene_prompts[i]["prompt"]],
                        progress=True,
                    )

            filename = os.path.join(utils.MUSIC_PATH, f"music-{i+1}.wav")
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
