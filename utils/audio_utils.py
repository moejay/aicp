import numpy as np
from pydub import AudioSegment
from io import BytesIO


def numpy_to_audiosegment(array, sample_rate=44100):
    """
    Convert a numpy array to a pydub.AudioSegment.

    Parameters:
    - array (numpy.ndarray): The numpy array to convert.
    - sample_rate (int): The sample rate of the audio (default is 44100).

    Returns:
    - pydub.AudioSegment: The resulting AudioSegment object.
    """
    # Ensure array is mono (1 channel)
    if len(array.shape) > 1:
        array = array.mean(axis=1)

    # Convert to PCM_16 format
    array = (array * 32767).astype(np.int16)

    # Create an AudioSegment
    audio = AudioSegment(
        array.tobytes(),
        frame_rate=sample_rate,
        sample_width=array.dtype.itemsize,
        channels=1,
    )

    # Export to WAV format and then re-import to ensure proper WAV header
    buffer = BytesIO()
    audio.export(buffer, format="wav")
    buffer.seek(0)
    audio = AudioSegment.from_wav(buffer)

    return audio
