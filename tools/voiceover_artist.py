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

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        # First rewerite the script in the voiceactor's voice
        llm = llms.RevGPTLLM(model=utils.get_config()["voiceover_artist"]["model"])
        template = open("prompts/voiceover_artist.txt").read()
        voice_actor = utils.get_config()["voiceover_artist"]["voice_actor"]
        vo = yaml.load(open(f"voiceover_actors/{voice_actor}/vo.yaml").read(), Loader=yaml.Loader)
        system_message_prompt = SystemMessagePromptTemplate.from_template(template)
        human_message_prompt = HumanMessagePromptTemplate.from_template("{script}")

        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

        chain = LLMChain(llm=llm, prompt=chat_prompt)
        # Since we only have narrator at this point, no dialogue
        script_input = yaml.dump([{ "narrator": s["narrator"]} for s in utils.get_script()])

        response = chain.run(characteristics=vo["characteristics"],
                           character_name=vo["name"],
                           script=script_input)

        # Use only the narrator lines to save tokens
        updated_scenes = []
        for updated, old in zip(json.loads(response), utils.get_scenes()):
            print(updated)
            updated_scene = old
            updated_scene.content = updated[vo["name"]]
            updated_scenes.append(updated_scene)
        # Save the updated script
        with open(f"{utils.SCRIPT}.voiceover", "w") as f:
            f.write(yaml.dump(updated_scenes))

        # then generate the voiceover
        preload_models()
        GEN_TEMP = 0.7
        SPEAKER = f"voiceover_actors/{voice_actor}/vo.npz"
        silence = np.zeros(int(0.25 * SAMPLE_RATE))
        pieces = []
        timecodes = [0] # Start at 0
        for scene in updated_scenes:
            print(f"Generating voiceover for scene {scene.scene_title}")
            sentences = nltk.sent_tokenize(scene.content)    
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
