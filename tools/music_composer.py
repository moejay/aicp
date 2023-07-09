import os
import math
import yaml
import logging

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

logger = logging.getLogger(__name__)


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
        prompt_params = parsers.get_params_from_prompt(cast_member.prompt)
        # This is in addition to the input (Human param)
        # Resolve params from existing config/director/program
        params = {}
        for param in prompt_params:
            params[param] = parsers.resolve_param_from_video(
                video=self.video, param_name=param
            )
        script_input = yaml.dump(
            [{"description": s["description"]} for s in parsers.get_script()]
        )
        params["input"] = yaml.dump(script_input)

        retries = 3
        while retries > 0:
            try:
                response = chain.run(
                    **params,
                )
                print(response)
                parsed = yaml.load(response, Loader=yaml.Loader)
                if len(parsed) != len(parsers.get_scenes()):
                    raise Exception("Number of scenes does not match")
                # Save the updated script
                with open(
                    os.path.join(utils.PATH_PREFIX, "music_prompts.yaml"), "w"
                ) as f:
                    f.write(response)

                return parsed
            except Exception as e:
                retries -= 1
                logger.warning(e)

        logger.error("Failed to generate music prompts, retries exhausted")
        raise Exception("Failed to generate music prompts, retries exhausted")

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

            # Generate music in 30 second chunks for each scene, but no chunks shorter than 8 seconds
            last_chunk_duration = scene.duration % 30
            num_chunks = math.ceil(scene.duration / 30)
            if last_chunk_duration < 8:
                num_chunks -= 1
            # Make sure there is at least one chunk
            num_chunks = max(1, num_chunks)

            for j in range(num_chunks):
                chunk_duration = 30
                if j == num_chunks - 1:
                    chunk_duration = last_chunk_duration
                model.set_generation_params(
                    use_sampling=True, top_k=250, duration=chunk_duration
                )

                output = model.generate(
                    descriptions=[self.scene_prompts[i]["prompt"]],
                    progress=True,
                )

                filename = os.path.join(utils.MUSIC_PATH, f"music-{i+1}-{j+1}.wav")
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
