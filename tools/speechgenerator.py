#!/usr/bin/env python

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool
from typing import Optional, Type

import nltk
import numpy as np
from scipy.io import wavfile

from bark.generation import (
        generate_text_semantic,
        preload_models
        )
from bark.api import semantic_to_waveform
from bark import SAMPLE_RATE

class SpeechGeneratorTool(BaseTool):
    name = "speechgenerator"
    description = "Useful when you need to generate speech for the script"

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        preload_models()
        script_lines = open("script.txt", "r").readlines()
        script_lines = [line if not line.lower().startswith("[scene") else "[SCENE]." for line in script_lines]
        script = "\n".join(script_lines)
        script = script.replace("\n", " ").strip()
        sentences = nltk.sent_tokenize(script)
        GEN_TEMP = 0.6
        SPEAKER = "v2/en_speaker_6"
        silence = np.zeros(int(0.25 * SAMPLE_RATE))
        pieces = []
        scenes = []
        for sentence in sentences:
            if sentence == "[SCENE].":
                scenes.append(sum([len(p)/SAMPLE_RATE for p in pieces]))
                continue
            semantic_tokens = generate_text_semantic(
                    sentence,
                    history_prompt=SPEAKER,
                    temp=GEN_TEMP,
                    min_eos_p=0.05
                )
            audio_array = semantic_to_waveform(semantic_tokens, history_prompt=SPEAKER)
            pieces += [audio_array, silence]
        full_audio = np.concatenate(pieces)
        int_audio_arr = (full_audio * np.iinfo(np.int16).max).astype(np.int16)
        wavfile.write("script.wav", SAMPLE_RATE, int_audio_arr)
        with open("script_timecodes.txt", "w") as f:
            f.write("\n".join([str(scene) for scene in scenes]))

        return "Done generating speech audio"

    def _arun(self, query:str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")
