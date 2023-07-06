import os
import subprocess

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from pydub import AudioSegment
from typing import Optional
from utils.parsers import get_scenes
from utils import utils

from .base import AICPBaseTool

def pad_audio_with_fade(audio_path, output_path, fade_duration, silence_duration):
    """Pad the wav file, fade out and add silence at the end."""
    audio = AudioSegment.from_wav(audio_path)
    audio = audio.fade_out(fade_duration)
    audio = audio + AudioSegment.silent(duration=silence_duration)
    audio.export(output_path, format="wav")

def combine_music_with_crossfade(music_paths, output_path, crossfade_duration=1.5):
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

    # Boost volume  (+db)
    background_music = background_music + 6
    voiceover = voiceover + 12

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
            # Find next speech segment and make hold_counter the half of the distance
            for j in range(i + 1, num_chunks):
                if is_speech[j]:
                    hold_counter = (j - i) // 2
                    break

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

class SoundEngineerTool(AICPBaseTool):
    name = "soundengineer"
    description = "Useful when you need to create the final audio for the video"

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None ) -> str:
        """Use the tool."""

        scenes = get_scenes()
        music_files = []
        for i, scene in enumerate(scenes):
            filename = os.path.join(utils.MUSIC_PATH, f"music-{i+1}.wav")
            music_files.append(filename)
            if scene.duration > 30:
                pad_audio_with_fade(filename, filename, 1000, 1000 * (scene.duration -  30))

        combine_music_with_crossfade(music_files, os.path.join(utils.MUSIC_PATH, "music.wav"))

        voiceover = AudioSegment.from_file(utils.VOICEOVER_WAV_FILE)
        background_music = AudioSegment.from_file(os.path.join(utils.MUSIC_PATH, "music.wav"))

        # Improve audio quality of voiceover
        voiceover += 9

        # Lower gain on background music
        average_loudness_voiceover = voiceover.dBFS
        max_loudness_background_music = background_music.max_dBFS
        desired_loudness_background_music = average_loudness_voiceover - 3
        gain_change = desired_loudness_background_music - max_loudness_background_music
        background_music = background_music.apply_gain(gain_change)

        # Mix audio together
        combined = voiceover.overlay(background_music)
        combined.fade_in(400)
        combined.fade_out(400)
        combined.export(utils.FINAL_AUDIO_FILE, format="wav")

        return "Done generating final audio"

    def _arun(self, query:str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        raise NotImplementedError("Async version of this tool is not implemented")
