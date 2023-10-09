#!/usr/bin/env python
import logging
import json
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from typing import Optional
import os
import librosa
import nltk
import numpy as np
import torch
from scipy.io import wavfile

from bark.generation import preload_models, clean_models
from utils import utils, llms, parsers, voice_gen
import math
import yaml
from .base import AICPBaseTool
from models import Actor, Scene

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
        all_scenes = parsers.get_scenes()

        num_scenes_per_group = 3
        # Split and do num_scenes_per_group scenes at a time
        scenes = []
        for i in range(0, len(all_scenes), num_scenes_per_group):
            scenes.append(all_scenes[i : i + num_scenes_per_group])

        # Generate the prompts
        all_prompts = []
        for scene_group, some_scenes in enumerate(scenes):
            # If we have a cached version, use that
            cached_file = os.path.join(
                utils.VOICEOVER_PATH, f"voiceover_prompts-{scene_group}.yaml"
            )
            if os.path.exists(cached_file):
                with open(cached_file) as f:
                    print(f"Loading cached prompts for scenes {scene_group}")
                    parts = yaml.load(f.read(), Loader=yaml.Loader)
                    all_prompts.extend(parts)
                    continue
            parts = self._call_llm(some_scenes)
            # Cache parts to file
            with open(cached_file, "w") as f:
                f.write(yaml.dump(parts))

            all_prompts.extend(parts)

        with open(os.path.join(utils.PATH_PREFIX, "voiceover_prompts.yaml"), "w") as f:
            f.write(yaml.dump(all_prompts))
        return all_prompts

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
                            f"scene_{scene_index:02}_line_{line_index:02}_{sentence_index:02}.wav",
                        )
                        if os.path.exists(sentence_wav_file):
                            print("Skipping line...")
                            # Load wav file as a piece
                            audio_array, _ = librosa.load(
                                sentence_wav_file, sr=voice_gen.NEW_SAMPLE_RATE
                            )

                            pieces += [audio_array]
                            continue

                        take_to_save = voice_gen.generate_speech_as_takes(
                            sentence,
                            history_prompt=actor.speaker,
                            text_temp=actor.speaker_text_temp,
                            waveform_temp=actor.speaker_waveform_temp,
                            max_takes=10,
                            save_all_takes=True,
                            speech_wpm=actor.speaker_wpm,
                            output_dir=utils.VOICEOVER_PATH,
                            output_file_prefix=f"scene_{scene_index:02}_line_{line_index:02}_{sentence_index:02}-take",
                        )
                        audio_array = take_to_save[0]

                        concatenated_take = np.concatenate([audio_array, silence])
                        pieces += [audio_array, silence]
                        voice_gen.save_audio_signal_wav(
                            concatenated_take,
                            voice_gen.NEW_SAMPLE_RATE,
                            sentence_wav_file,
                        )
                        # Save the result of the take
                        with open(sentence_wav_file.replace(".wav", ".json"), "w") as f:
                            # Update the duration to take into account the silence
                            take_to_save[2]["duration"] = (
                                len(concatenated_take) / voice_gen.NEW_SAMPLE_RATE
                            )
                            # Update the actor name value
                            take_to_save[2]["actor"] = actor.name
                            json.dump(take_to_save[2], f, indent=4)

                timecodes.append(
                    math.ceil(sum([len(p) / voice_gen.NEW_SAMPLE_RATE for p in pieces]))
                )

            full_audio = np.concatenate(pieces)
            int_audio_arr = (full_audio * np.iinfo(np.int16).max).astype(np.int16)
            wavfile.write(
                utils.VOICEOVER_WAV_FILE, voice_gen.NEW_SAMPLE_RATE, int_audio_arr
            )

        if os.path.exists(utils.VOICEOVER_SUBTITLES):
            print("Skipping subtitles generation...")
        else:
            full_transcription = voice_gen.get_whisper_model().transcribe(
                utils.VOICEOVER_WAV_FILE, word_timestamps=True
            )

            with open(utils.VOICEOVER_SUBTITLES, "w") as f:
                srt_data = voice_gen.generate_ass(
                    full_transcription,
                    self.video.production_config.subtitles_fontname,
                    self.video.production_config.subtitles_fontsize,
                    self.video.production_config.subtitles_alignment,
                )
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

    def _call_llm(self, scenes: list[Scene]) -> list:
        cast_member = self.video.director.get_voiceover_artist()
        chain = llms.get_llm(model=cast_member.model, template=cast_member.prompt)
        prompt_params = parsers.get_params_from_prompt(cast_member.prompt)
        # Resolve params from existing config/director/program
        params = {}
        for param in prompt_params:
            params[param] = parsers.resolve_param_from_video(
                video=self.video, param_name=param
            )

        cast_member = self.video.director.get_voiceover_artist()
        chain = llms.get_llm(model=cast_member.model, template=cast_member.prompt)
        retries = 3
        params["input"] = yaml.dump(
            [
                {
                    "scene_title": scene.scene_title,
                    "scene_description": scene.description,
                    "scene_lines": [
                        {
                            "actor": line.actor.name,
                            "line": line.line,
                        }
                        for line in scene.dialogue
                    ],
                }
                for scene in scenes
            ]
        )
        while retries > 0:
            try:
                response = chain.run(
                    **params,
                )
                print(response)
                parsed = yaml.load(response, Loader=yaml.Loader)
                if len(parsed) != len(scenes):
                    raise Exception("Number of scenes does not match")
                # Make sure it's an array of arrays that include actor and line
                for converted_scene in parsed:
                    for converted_dialogue in converted_scene:
                        if "actor" not in converted_dialogue:
                            raise Exception("Actor not found in converted dialogue")
                        if "line" not in converted_dialogue:
                            raise Exception("Line not found in converted dialogue")
                return parsed
            except Exception as e:
                retries -= 1
                if retries == 0:
                    raise e
                print("Retrying...")
        raise Exception("Failed to convert")
