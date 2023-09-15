import numpy as np
from pydub import AudioSegment
from io import BytesIO


def get_audio_file_length(path: str) -> float:
    """Get the length of an audio file in seconds."""
    return AudioSegment.from_file(path).duration_seconds

def mix_audio_files(audio_files: list[str], output_path: str) -> None:
    """Mix audio files together."""
    combined = AudioSegment.empty()
    for idx, audio_file in enumerate(audio_files):
        if idx == 0:
            combined = AudioSegment.from_file(audio_file)
            continue
        combined = combined.overlay(AudioSegment.from_file(audio_file))
    combined.export(output_path, format="wav")