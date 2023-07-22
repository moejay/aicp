#!/usr/bin/env python
import logging
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from typing import Optional
import os
import librosa
import nltk
import numpy as np
from df import enhance, init_df
import torch
from scipy.io import wavfile

from bark.generation import preload_models, clean_models
from utils import utils, llms, parsers, voice_gen
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

    def concatenate_and_remove(self, arr, target):
        i = 1  # start from second element
        while i < len(arr):
            if arr[i] == target:
                arr[i - 1] += target  # concatenate target to the previous string
                arr.pop(i)  # remove the target
            else:
                i += 1  # move to the next element
        return arr

    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        # initialize
        self.initialize_agent()

        # then generate the voiceover
        preload_models()
        silence = np.zeros(int(0.25 * voice_gen.NEW_SAMPLE_RATE))
        pieces = []
        timecodes = [0]  # Start at 0

        # dont recreate voiceover, its expensive
        if os.path.exists(utils.VOICEOVER_WAV_FILE):
            print("Skipping VO generation...")
        else:
            model, df_state, _ = init_df()

            for scene_index, scene in enumerate(self.scene_prompts):
                print(f"--- SCENE: {scene_index + 1}/{len(self.scene_prompts)} ---")
                for line_index, item in enumerate(scene):
                    actor = Actor.from_name(item["actor"])
                    sentences = nltk.sent_tokenize(item["line"])

                    # It's way more likely to get a good laugh if it's in the sentence
                    # We get a lot more "just noise" if it is a separate token
                    non_word_tokens = [
                        "[laughs]",
                        "[sighs]",
                        "[clears throat]",
                        "[gasps]",
                        "[coughs]",
                    ]
                    for token in non_word_tokens:
                        sentences = self.concatenate_and_remove(sentences, token)

                    for sentence_index, sentence in enumerate(sentences):
                        print(f"{actor.name}: {sentence}")
                        sentence_wav_file = os.path.join(
                            utils.VOICEOVER_PATH,
                            f"scene_{scene_index}_line_{line_index}_{sentence_index}.wav",
                        )
                        if os.path.exists(sentence_wav_file):
                            print("Skipping line...")
                            # Load wav file as a piece
                            audio_array, _ = librosa.load(
                                sentence_wav_file, sr=voice_gen.NEW_SAMPLE_RATE
                            )
                            pieces += [audio_array, silence]
                            continue

                        audio_array = voice_gen.generate_speech_as_takes(
                            sentence,
                            history_prompt=actor.speaker,
                            text_temp=actor.speaker_text_temp,
                            waveform_temp=actor.speaker_waveform_temp,
                            max_takes=40,
                            save_all_takes=True,
                            output_dir=utils.VOICEOVER_PATH,
                            output_file_prefix=f"scene_{scene_index}_line_{line_index}_{sentence_index}-take",
                        )
                        if actor.speaker_enhance:
                            audio_array = enhance(
                                model, df_state, torch.tensor([audio_array])
                            )
                        pieces += [audio_array, silence]
                        voice_gen.save_audio_signal_wav(
                            audio_array, voice_gen.NEW_SAMPLE_RATE, sentence_wav_file
                        )

                timecodes.append(
                    math.ceil(sum([len(p) / voice_gen.NEW_SAMPLE_RATE for p in pieces]))
                )

            full_audio = np.concatenate(pieces)
            int_audio_arr = (full_audio * np.iinfo(np.int16).max).astype(np.int16)
            wavfile.write(
                utils.VOICEOVER_WAV_FILE, voice_gen.NEW_SAMPLE_RATE, int_audio_arr
            )
            full_transcription = voice_gen.get_whisper_model().transcribe(
                utils.VOICEOVER_WAV_FILE, word_timestamps=True
            )

            with open(utils.VOICEOVER_SUBTITLES, "w") as f:
                srt_data = voice_gen.generate_ass(full_transcription)
                f.write(srt_data)

            with open(utils.VOICEOVER_TIMECODES, "w") as f:
                f.write("\n".join(map(str, timecodes)))

        # Due to bug in clean_models
        while True:
            try:
                clean_models()
                break
            except:
                pass
        torch.cuda.empty_cache()

        return "Done generating voiceover audio"

    def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")
