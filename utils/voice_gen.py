from bark import SAMPLE_RATE, api
from scipy.io import wavfile
import nltk
import numpy as np


def generate_audio_from_sentence(
    sentence, speaker, output_file, output_full, text_temp=0.6, waveform_temp=0.6
):
    print(f"Generating audio for {speaker}")
    print(f"Generating sentence: {sentence}")
    out = api.generate_audio(
        sentence,
        history_prompt=speaker,
        silent=True,
        text_temp=text_temp,
        waveform_temp=waveform_temp,
        output_full=output_full,
    )
    out_arr = out
    if output_full:
        out_arr = out[1]

    int_audio_arr = (out_arr * np.iinfo(np.int16).max).astype(np.int16)
    wavfile.write(output_file, SAMPLE_RATE, int_audio_arr)
    output_npz_file = None
    if output_full:
        output_npz_file = output_file.replace(".wav", ".npz")
        api.save_as_prompt(output_npz_file, out[0])
    return output_file, output_npz_file
