from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool
from typing import Optional, Type
from langchain import OpenAI
import json
from utils.utils import get_scenes, get_script
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write
from pydub import AudioSegment
import subprocess
from utils import utils

def combine_music_with_crossfade(music_paths, output_path, crossfade_duration=3):
    """
    Combine multiple music clips into a single file with crossfade.

    :param music_paths: List of paths to the music clips.
    :param output_path: Path to the output file.
    :param crossfade_duration: Duration of the crossfade in seconds (default is 3 seconds).
    """

    # Basic input string
    input_str = ""
    
    # Building the input string
    for music_path in music_paths:
        input_str += f" -i {music_path}"

    # Building filter_complex string
    filter_complex_str = ""
    for i in range(1, len(music_paths)):
        if i == 1:
            filter_complex_str += f"[0:a][{i}:a]acrossfade=d={crossfade_duration}:c1=tri:c2=squ[ac{i}];"
        else:
            filter_complex_str += f"[ac{i-1}][{i}:a]acrossfade=d={crossfade_duration}:c1=tri:c2=squ[ac{i}];"
    
    # Removing last semicolon
    filter_complex_str = filter_complex_str.rstrip(';')

    # Building the final FFmpeg command
    cmd = f"ffmpeg {input_str} -filter_complex \"{filter_complex_str}\" -map \"[ac{len(music_paths) - 1}]\" {output_path}"

    # Run the FFmpeg command
    subprocess.run(cmd, shell=True)


def duck(voiceover_path, music_path, output_path, duck_dB=-10.0, threshold=-40, chunk_duration=100, fade_duration=500, hold_duration=500):
    """
    Perform audio ducking: lower the volume of the background music during speech segments in the voiceover.

    :param voiceover_path: Path to the voiceover audio file.
    :param music_path: Path to the background music file.
    :param output_path: Path where the output file should be saved.
    :param duck_dB: The level to duck the background music in dB (default is -10.0 dB).
    :param threshold: Threshold for detecting speech in dB (default is -40 dB).
    :param chunk_duration: Chunk duration in milliseconds used for speech detection (default is 100 ms).
    :param fade_duration: Duration in milliseconds for fade-in and fade-out (default is 500 ms).
    :param hold_duration: Duration in milliseconds to keep the ducking after speech ends (default is 500 ms).
    """

    # Load the audio files
    voiceover = AudioSegment.from_file(voiceover_path)
    background_music = AudioSegment.from_file(music_path)

    # Analyze voiceover to find segments of speech
    num_chunks = len(voiceover) // chunk_duration
    is_speech = [voiceover[i * chunk_duration : (i + 1) * chunk_duration].dBFS > threshold for i in range(num_chunks)]

    # Duck the background music during speech
    output = AudioSegment.empty()
    last_chunk_was_speech = False
    hold_counter = 0
    for i, speech in enumerate(is_speech):
        chunk_start = i * chunk_duration
        chunk_end = (i + 1) * chunk_duration
        chunk = background_music[chunk_start : chunk_end]

        if speech:
            ducked_chunk = chunk + duck_dB
            if not last_chunk_was_speech:
                ducked_chunk = ducked_chunk.fade_in(fade_duration)
            output += ducked_chunk
            hold_counter = hold_duration // chunk_duration
        else:
            if last_chunk_was_speech or hold_counter > 0:
                output += (chunk + duck_dB).fade_out(fade_duration) if hold_counter == 0 else chunk + duck_dB
                hold_counter = max(0, hold_counter - 1)
            else:
                output += chunk

        last_chunk_was_speech = speech

    # Combine the voiceover and background music
    combined = voiceover.overlay(output)

    # Save the final output
    combined.export(output_path, format="wav")

class MusicConductorTool(BaseTool):
    name = "musicconductor"
    description = "Useful when you need to generate a music score for the script"

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""

        llm = OpenAI(temperature=0.5)
        response = llm(f"""
                Given the following script,
            your task is to analyze the general mood of the script and create appropriate 
            background music for it.
            You should generate one description per scene in the script.

            Respond in the following format (JSON array) and one prompt per scene.

            [
                "Upbeat rock guitar solo, with modern electronic music elements",
                "Slow classical cello playing with city scape background",
                ...
            ]


            Here is the script, make sure you respond in valid JSON, and only respond with the music descriptions:
            {get_script()}
        """)

        music_prompts = json.loads(response)
        scenes = get_scenes()
        if len(music_prompts) < len(scenes):
            return "Please try again, not enough music prompts"
        model = MusicGen.get_pretrained("medium")
        music_outputs = []
        for scene, mp in zip(scenes, music_prompts):
            model.set_generation_params(
                    use_sampling=True,
                    top_k=250,
                    duration=min(30, scene.duration)
                    )
            music_outputs.append(
                    model.generate(
                        descriptions=[mp],
                        progress=True,
                        )
                    )

        music_files = []
        for i, s in enumerate(music_outputs):
            filename = f"music-{i}.wav"
            music_files.append(filename)
            audio_write(filename,
                    s[0].to("cpu"), 
                    model.sample_rate,
                    strategy="loudness",
                    loudness_headroom_db=16,
                    add_suffix=False)

        combine_music_with_crossfade(music_files, "music.wav")

        duck(utils.VOICEOVER_WAV_FILE, "music.wav", utils.FINAL_AUDIO_FILE, chunk_duration=1000, hold_duration=1500)
        return "Done generating music score"


    def _arun(self, query:str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        raise NotImplementedError("Async version of this tool is not implemented")
