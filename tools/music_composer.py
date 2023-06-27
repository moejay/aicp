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

class MusicComposerTool(BaseTool):
    name = "musiccomposer"
    description = "Useful when you need to generate a music score for the script"

    def ego(self):
        llm = llms.RevGPTLLM(model=utils.get_config()["music_composer"]["ego_model"])

        template = open("prompts/music_composer.txt").read()
        system_message_prompt = SystemMessagePromptTemplate.from_template(template)
        human_message_prompt = HumanMessagePromptTemplate.from_template("{script}")

        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

        chain = LLMChain(llm=llm, prompt=chat_prompt) 
        script_input = yaml.dump([{ "description": s["description"]} for s in utils.get_script()])

        response = chain.run(
                script=script_input
            )
        print(response)

        music_prompts = json.loads(response)
        scenes = get_scenes()

        if len(music_prompts) < len(scenes):
            return "Please try again, not enough music prompts"
        else:
            return music_prompts

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        music_prompts = self.ego()
        scenes = get_scenes()

        model = MusicGen.get_pretrained("medium")

        for i, ( scene, mp ) in enumerate(zip(scenes, music_prompts)):
            print(f"SCENE: {scene}")
            print(f"PROMPT: {mp}")
            model.set_generation_params(
                        use_sampling=True,
                        top_k=250,
                        duration=min(30, scene.duration)
                    )
            output = model.generate(
                        descriptions=[mp["prompt"]],
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
