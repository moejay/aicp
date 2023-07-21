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
import whisper
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

NEW_SAMPLE_RATE = 44100

WHISPER_MODEL = None


def generate_ass(transcription_data):
    """
    Generate a ASS file content based on the transcription data.

    Parameters:
    transcription_data (dict): Transcription data including word-level timestamps.

    Returns:
    str: Content of the ASS file.
    """
    # ASS file header
    ass_content = """[Script Info]
ScriptType: v4.00+
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,26,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,1,1,0,0,100,100,0,0,1,2,2,2,10,10,10,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    for i, segment in enumerate(transcription_data["segments"], start=1):
        for word in segment["words"]:
            # Convert start and end times to HH:MM:SS.mm format
            start_time = format_time(word["start"])
            end_time = format_time(word["end"])
            # Add this subtitle to the ASS content
            ass_content += (
                f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{word['word']}\n"
            )
    return ass_content


def format_time(seconds):
    """
    Convert a time in seconds to ASS time format.

    Parameters:
    seconds (float): Time in seconds.

    Returns:
    str: Time in ASS format (H:MM:SS.mm).
    """
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    # Convert to milliseconds and round to 2 decimal places
    milliseconds = round((seconds % 1) * 100)
    # Remove the decimal part from seconds
    seconds = int(seconds)
    # Return in ASS format
    return f"{int(hours)}:{int(minutes):02}:{seconds:02}.{milliseconds:02}"


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


def compute_similarity(str1, str2):
    # Load BERT model
    model = SentenceTransformer("bert-base-nli-mean-tokens")

    # Compute embeddings
    embeddings = model.encode([str1, str2])

    # Compute cosine similarity
    cosine_sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

    return cosine_sim * 100


def get_whisper_model():
    global WHISPER_MODEL
    if WHISPER_MODEL is None:
        WHISPER_MODEL = whisper.load_model("base.en")
    return WHISPER_MODEL


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
    audio_resampled = torchaudio.functional.resample(
        vocos_output, orig_freq=SAMPLE_RATE, new_freq=NEW_SAMPLE_RATE
    )
    whisper_resampled = torchaudio.functional.resample(
        audio_resampled, orig_freq=NEW_SAMPLE_RATE, new_freq=16000
    )
    transcribed_text = get_whisper_model().transcribe(whisper_resampled[0])["text"]
    text_similarity = compute_similarity(sentence, transcribed_text)
    audio = audio_resampled.cpu().numpy()[0]
    snr = compute_snr(audio)
    duration = len(audio) / NEW_SAMPLE_RATE

    results = {
        "sentence": sentence,
        "transcribed_text": transcribed_text,
        "text_similarity": text_similarity,
        "duration": duration,
        "text_temp": text_temp,
        "waveform_temp": waveform_temp,
        "history_prompt": history_prompt,
        "snr": snr,
    }
    print(
        f"""
    snr: {snr} 
    transcribed_text: {transcribed_text}
    text_similarity: {text_similarity}
    duration: {duration}"""
    )
    if (snr < 20 or snr > 28) or duration > 9 or text_similarity < 90:
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
