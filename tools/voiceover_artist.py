#!/usr/bin/env python

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool
from typing import Optional, Type
import os
import nltk
import numpy as np
from scipy.io import wavfile

from bark.generation import (
        generate_text_semantic,
        preload_models,
        clean_models
        )
from bark.api import semantic_to_waveform
from bark import SAMPLE_RATE
from utils import utils, llms
import math
import yaml
import json
from langchain import LLMChain
from langchain.prompts.chat import (ChatPromptTemplate, SystemMessagePromptTemplate, AIMessagePromptTemplate, HumanMessagePromptTemplate)


class VoiceOverArtistTool(BaseTool):
    name = "voiceoverartist"
    description = "Useful when you need to generate a voiceover for the script"

    actor = {}
    speaker = ""
    scene_prompts = []


    def initialize_agent(self):
        self.load_actor()
        self.load_prompts()

    def load_actor(self):
        """ Load voice actor specific files and configuration """
        actor = utils.get_config()["voiceover_artist"]["actor"]
        with open(os.path.join(utils.ACTOR_PATH, f"{actor}.yaml")) as f:
            print(f"Loading VO actor: {actor}")
            self.actor = yaml.load(f.read(), Loader=yaml.Loader)

        self.speaker = self.actor["speaker"]

    def load_prompts(self):
        # load voiceover artist prompts if they exist or create them 
        prompts_file = os.path.join(utils.PATH_PREFIX, "voiceover_prompts.json")
        if os.path.exists(prompts_file):
            with open(prompts_file) as prompts:
                print("Loading existing prompt file: voiceover_prompts")
                self.scene_prompts = json.loads(prompts.read().strip())
        else:
            print("Generating new dialog prompts...")
            self.scene_prompts = self.ego()

    def ego(self):
        """ Personalize the dialog according to the selected voice actor """
        llm = llms.RevGPTLLM(model=utils.get_config()["voiceover_artist"]["ego_model"])

        template = open("prompts/voiceover_artist.txt").read()
        system_message_prompt = SystemMessagePromptTemplate.from_template(template)
        human_message_prompt = HumanMessagePromptTemplate.from_template("{script}")

        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
        chain = LLMChain(llm=llm, prompt=chat_prompt)

        # Since we only have narrator at this point, no dialogue
        script_input = yaml.dump([{ "narrator": s["narrator"]} for s in utils.get_script()])

        response = chain.run(
                character_bio=self.actor["character_bio"],
                script=script_input
            )
        print(response)

        # Save the updated script
        with open(os.path.join(utils.PATH_PREFIX, "voiceover_prompts.json"), "w") as f:
            f.write(response)

        return response
           
    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        # initialize
        self.initialize_agent()

        # then generate the voiceover
        preload_models()
        GEN_TEMP = 0.7
        SPEAKER = self.speaker
        silence = np.zeros(int(0.25 * SAMPLE_RATE))
        pieces = []
        timecodes = [0] # Start at 0

        # dont recreate voiceover, its expensive
        if os.path.exists(utils.VOICEOVER_WAV_FILE):
            print("Skipping VO generation...")
        else:
            for scene in self.scene_prompts:
                print("--- SCENE ---")
                print(f"DIALOG: {scene['dialog']}")
    
                sentences = nltk.sent_tokenize(scene['dialog'])    
                for sentence in sentences:
                    semantic_tokens = generate_text_semantic(
                            sentence,
                            history_prompt=SPEAKER,
                            temp=GEN_TEMP,
                            min_eos_p=0.05
                        )
                    audio_array = semantic_to_waveform(semantic_tokens, history_prompt=SPEAKER)
                    pieces += [audio_array, silence]
                timecodes.append(math.ceil(sum([len(p)/SAMPLE_RATE for p in pieces])))

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

    def _arun(self, query:str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")
