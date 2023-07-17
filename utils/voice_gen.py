import os
from typing import Optional, Union, Dict
import numpy as np
from bark.generation import generate_coarse, generate_fine
import json
from bark import SAMPLE_RATE, api, text_to_semantic
from scipy.io import wavfile
import numpy as np
import torch
import torchaudio
from vocos import Vocos

NEW_SAMPLE_RATE = 44100


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


def compute_snr(audio_signal):
    """
    Compute the Signal-to-Noise Ratio (SNR) of an audio signal.

    Parameters:
    audio_signal (np.array): The audio signal.

    Returns:
    float: The SNR of the audio signal in decibels.
    """

    # Compute the Fast Fourier Transform (FFT)
    fft = np.fft.fft(audio_signal)

    # Compute the Power Spectral Density (PSD)
    psd = np.abs(fft) ** 2

    # Define the threshold as the mean power
    threshold = np.mean(psd)

    # Separate the signal and the noise
    signal_psd = psd[psd > threshold]
    noise_psd = psd[psd <= threshold]

    # Compute the Signal-to-Noise Ratio (SNR)
    snr = 10 * np.log10(np.mean(signal_psd) / np.mean(noise_psd))

    return snr


def generate_speech(sentence, history_prompt, text_temp, waveform_temp):
    print(f"Generating sentence: {sentence}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    vocos = Vocos.from_pretrained("charactr/vocos-encodec-24khz").to(device)

    semantic_tokens = text_to_semantic(
        sentence, history_prompt=history_prompt, temp=text_temp, silent=True
    )
    audio_tokens = semantic_to_audio_tokens(
        semantic_tokens,
        history_prompt=history_prompt,
        temp=waveform_temp,
        silent=True,
        output_full=False,
    )
    audio_tokens_torch = torch.from_numpy(audio_tokens).to(device)
    features = vocos.codes_to_features(audio_tokens_torch)
    vocos_output = vocos.decode(features, bandwidth_id=torch.tensor([2], device=device))
    audio = (
        torchaudio.functional.resample(
            vocos_output, orig_freq=SAMPLE_RATE, new_freq=NEW_SAMPLE_RATE
        )
        .cpu()
        .numpy()[0]
    )

    snr = compute_snr(audio)
    duration = len(audio) / NEW_SAMPLE_RATE

    results = {
        "sentence": sentence,
        "duration": duration,
        "text_temp": text_temp,
        "waveform_temp": waveform_temp,
        "history_prompt": history_prompt,
        "snr": snr,
    }
    print(
        f"""
    snr: {snr} 
    duration: {duration}"""
    )
    if (snr < 20 or snr > 28) or duration > 9:
        # Audio is noisy and or not clear
        print("We think it's bad")
        return audio, True, results

    print("We think it's good")
    return audio, False, results


def semantic_to_audio_tokens(
    semantic_tokens: np.ndarray,
    history_prompt: Optional[Union[Dict, str]] = None,
    temp: float = 0.7,
    silent: bool = False,
    output_full: bool = False,
):
    coarse_tokens = generate_coarse(
        semantic_tokens,
        history_prompt=history_prompt,
        temp=temp,
        silent=silent,
        use_kv_caching=True,
    )
    fine_tokens = generate_fine(coarse_tokens, history_prompt=history_prompt, temp=0.5)

    if output_full:
        full_generation = {
            "semantic_prompt": semantic_tokens,
            "coarse_prompt": coarse_tokens,
            "fine_prompt": fine_tokens,
        }
        return full_generation
    return fine_tokens


def generate_speech_as_takes(
    sentence,
    history_prompt,
    text_temp,
    waveform_temp,
    max_takes=100,
    save_all_takes=False,
    output_dir=None,
    output_file_prefix=None,
):
    current_take = 0
    takes = []

    while max_takes > 0:
        audio, is_bad, results = generate_speech(
            sentence, history_prompt, text_temp, waveform_temp
        )
        if save_all_takes:
            take_path = os.path.join(
                output_dir, f"{output_file_prefix}_{current_take}.wav"
            )
            save_audio_signal_wav(audio, NEW_SAMPLE_RATE, take_path)
            # Save results as well
            results_path = take_path.replace(".wav", ".json")
            with open(results_path, "w") as f:
                json.dump(results, f, indent=4)

        takes.append((audio, is_bad, results))
        current_take += 1
        if not is_bad:
            return audio
        print(f"Doing another take... {max_takes} left")
        max_takes -= 1

    # If we get here, find the best take and use that
    # Sorted by desc snr, then ascending duration
    sorted_takes = sorted(
        takes, key=lambda x: (x[2]["snr"], -x[2]["duration"]), reverse=True
    )
    best_take = sorted_takes[0]
    print(f"Best take: {best_take[2]}")
    return best_take[0]


def save_audio_signal_wav(audio_signal, sample_rate, output_file):
    # Convert the audio signal to a 16-bit integer array
    int_audio_signal = (audio_signal * np.iinfo(np.int16).max).astype(np.int16)
    wavfile.write(output_file, sample_rate, int_audio_signal)
