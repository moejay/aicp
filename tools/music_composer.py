import os
import yaml

from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from typing import Optional
from utils.parsers import get_scenes
from utils import utils, llms, parsers
from .base import AICPBaseTool


class MusicComposerTool(AICPBaseTool):
    name = "musiccomposer"
    description = "Useful when you need to generate a music score for the script"

    scene_prompts = []

    def initialize_agent(self):
        """Initialize the agent"""
        self.load_prompts()

    def load_prompts(self):
        # load voiceover artist prompts if they exist or create them
        prompts_file = os.path.join(utils.PATH_PREFIX, "music_prompts.yaml")
        if os.path.exists(prompts_file):
            with open(prompts_file) as prompts:
                print("Loading existing music prompts: music_prompts.yaml")
                self.scene_prompts = yaml.load(
                    prompts.read().strip(), Loader=yaml.Loader
                )
        else:
            print("Generating new music prompts...")
            self.scene_prompts = self.ego()

    def ego(self):
        cast_member = self.video.director.get_music_composer()
        chain = llms.get_llm(model=cast_member.model, template=cast_member.prompt)

        script_input = yaml.dump(
            [{"description": s["description"]} for s in parsers.get_script()]
        )

        response = chain.run(script_input)
        print(response)

        scene_prompts = yaml.load(response, Loader=yaml.Loader)
        scenes = get_scenes()

        if len(scene_prompts) < len(scenes):
            return "Please try again, not enough music prompts"

        # Save the prompts
        with open(os.path.join(utils.PATH_PREFIX, "music_prompts.yaml"), "w") as f:
            f.write(response)

        return scene_prompts

    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
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
                use_sampling=True, top_k=250, duration=min(30, scene.duration)
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
                add_suffix=False,
            )

        return "Done generating music score"

    def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        raise NotImplementedError("Async version of this tool is not implemented")
