#!/usr/bin/env python

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool
from typing import Optional, Type

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
from utils import utils

class VoiceOverArtistTool(BaseTool):
    name = "voiceoverartist"
    description = "Useful when you need to generate a voiceover for the script"

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        preload_models()
        GEN_TEMP = 0.8447
        SPEAKER = "v2/en_speaker_6"
        silence = np.zeros(int(0.25 * SAMPLE_RATE))
        pieces = []
		timecodes = [0] # Start at 0
		for scene in utils.get_scenes():
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
			timecodes.append(ceil(sum([len(p)/SAMPLE_RATE for p in pieces])))

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
