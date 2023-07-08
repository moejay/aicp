#!/usr/bin/env python
import logging
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from typing import Optional
import os
import nltk
import numpy as np
from scipy.io import wavfile

from bark.generation import generate_text_semantic, preload_models, clean_models
from bark.api import semantic_to_waveform
from bark import SAMPLE_RATE
from utils import utils, llms, parsers
import math
import yaml
from .base import AICPBaseTool
from models import Actor

logger = logging.getLogger(__name__)


class VoiceOverArtistTool(AICPBaseTool):
    name = "voiceoverartist"
    description = "Useful when you need to generate a voiceover for the script"

    actor = {}
    speaker = ""
    scene_prompts = []

    def initialize_agent(self):
        """Initialize the agent"""
        self.load_prompts()

    def load_prompts(self):
        # load voiceover artist prompts if they exist or create them
        prompts_file = os.path.join(utils.PATH_PREFIX, "voiceover_prompts.yaml")
        if os.path.exists(prompts_file):
            with open(prompts_file) as prompts:
                print("Loading existing prompt file: voiceover_prompts")
                self.scene_prompts = yaml.load(prompts.read(), Loader=yaml.Loader)
        else:
            print("Generating new dialog prompts...")
            self.scene_prompts = self.ego()

    def ego(self):
        """Personalize the dialog according to the selected voice actor"""
        cast_member = self.video.director.get_voiceover_artist()
        chain = llms.get_llm(model=cast_member.model, template=cast_member.prompt)
        prompt_params = parsers.get_params_from_prompt(cast_member.prompt)
        prompt_params.append("input")
        # This is in addition to the input (Human param)
        # Resolve params from existing config/director/program
        params = {}
        for param in prompt_params:
            params[param] = parsers.resolve_param_from_video(
                video=self.video, param_name=param
            )

        params["input"] = yaml.dump(parsers.get_scenes())

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
                # Make sure it's an array of arrays that include actor and line
                for converted_scene in parsed:
                    for converted_dialogue in converted_scene:
                        if "actor" not in converted_dialogue:
                            raise Exception("Actor not found in converted dialogue")
                        if "line" not in converted_dialogue:
                            raise Exception("Line not found in converted dialogue")

                # Save the updated script
                with open(
                    os.path.join(utils.PATH_PREFIX, "voiceover_prompts.yaml"), "w"
                ) as f:
                    f.write(response)

                return parsed
            except Exception as e:
                retries -= 1
                logger.warning(e)

        logger.error("Failed to generate voiceover prompts, retries exhausted.")
        raise Exception("Failed to generate voiceover prompts, retries exhausted.")

    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        # initialize
        self.initialize_agent()

        # then generate the voiceover
        preload_models()
        GEN_TEMP = 0.7
        silence = np.zeros(int(0.25 * SAMPLE_RATE))
        pieces = []
        timecodes = [0]  # Start at 0

        # dont recreate voiceover, its expensive
        if os.path.exists(utils.VOICEOVER_WAV_FILE):
            print("Skipping VO generation...")
        else:
            for scene in self.scene_prompts:
                print("--- SCENE ---")
                for item in scene:
                    actor = Actor.from_name(item["actor"])
                    sentences = nltk.sent_tokenize(item["line"])
                    for sentence in sentences:
                        semantic_tokens = generate_text_semantic(
                            sentence,
                            history_prompt=actor.speaker,
                            temp=GEN_TEMP,
                            min_eos_p=0.05,
                        )
                        audio_array = semantic_to_waveform(
                            semantic_tokens, history_prompt=actor.speaker
                        )
                        pieces += [audio_array, silence]
                timecodes.append(math.ceil(sum([len(p) / SAMPLE_RATE for p in pieces])))

            full_audio = np.concatenate(pieces)
            int_audio_arr = (full_audio * np.iinfo(np.int16).max).astype(np.int16)
            wavfile.write(utils.VOICEOVER_WAV_FILE, SAMPLE_RATE, int_audio_arr)

            with open(utils.VOICEOVER_TIMECODES, "w") as f:
                f.write("\n".join(map(str, timecodes)))

        # Due to bug in clean_models
        while True:
            try:
                clean_models()
                break
            except:
                pass

        return "Done generating voiceover audio"

    def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")
