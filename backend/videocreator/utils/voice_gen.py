import os
from typing import Optional, Union, Dict
import nltk
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

NEW_SAMPLE_RATE = 48000

WHISPER_MODEL = None


def generate_ass(transcription_data, fontname, fontsize, alignment):
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
Style: Default,{},{},&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,1,1,0,0,100,100,0,0,1,2,10,{},10,10,10,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""".format(
        fontname,
        fontsize,
        alignment,
    )

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


def non_silence_in_last_duration_audio(y, sr, duration_ms=250, silence_ratio=0.01):
    """
    Detect if there's any non-silence in the last specified duration of an audio array.

    Parameters:
    - y (numpy array): Audio time series.
    - sr (int): Sampling rate of the audio time series.
    - duration_ms (int): Duration in milliseconds to consider from the end of the audio. Default is 250ms.
    - silence_ratio (float): Ratio to define silence threshold based on max energy. Default is 0.01 (1% of max energy).

    Returns:
    - bool: True if there's non-silence in the specified duration, False otherwise.
    """

    # Compute short-time energy
    hop_length = 512
    frame_length = 2048
    energy = np.array(
        [sum(abs(y[i : i + frame_length] ** 2)) for i in range(0, len(y), hop_length)]
    )

    # Define a threshold for silence
    silence_threshold = silence_ratio * max(energy)

    # Consider the last specified duration of the audio
    num_frames_duration = int((duration_ms / 1000) * sr / hop_length)
    last_duration_start = max(0, len(energy) - num_frames_duration)

    # Check if there's any non-silence in the last duration
    return any(e > silence_threshold for e in energy[last_duration_start:])


def estimate_speech_duration_with_pauses(sentence, speaking_rate=150, comma_pause=0.5):
    """
    Estimate the duration to speak a given sentence, accounting for pauses introduced by commas.

    Parameters:
    - sentence (str): The sentence to be spoken.
    - speaking_rate (int): Average speaking rate in words per minute. Default is 150 wpm.
    - comma_pause (float): Duration in seconds to pause for each comma. Default is 0.5 seconds.

    Returns:
    - float: Estimated duration in seconds to speak the sentence.
    """

    # Count the number of words in the sentence
    num_words = len(sentence.split())

    # Count the number of commas in the sentence
    num_commas = sentence.count(",")

    # Compute the estimated duration considering the speaking rate and pauses for commas
    estimated_duration = (num_words / speaking_rate * 60) + (num_commas * comma_pause)

    return estimated_duration


def generate_speech(sentence, history_prompt, text_temp, waveform_temp, speech_wpm):
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
    has_non_silence = non_silence_in_last_duration_audio(audio, NEW_SAMPLE_RATE)
    duration = len(audio) / NEW_SAMPLE_RATE
    max_duration = estimate_speech_duration_with_pauses(
        sentence, speaking_rate=speech_wpm
    )

    results = {
        "sentence": sentence,
        "transcribed_text": transcribed_text,
        "has_non_silence": has_non_silence,
        "text_similarity": text_similarity,
        "duration": duration,
        "max_duration": max_duration,
        "text_temp": text_temp,
        "waveform_temp": waveform_temp,
        "history_prompt": history_prompt,
        "snr": snr,
    }
    print(
        f"""
    snr: {snr}
    transcribed_text: {transcribed_text}
    has_non_silence: {has_non_silence}
    text_similarity: {text_similarity}
    duration: {duration}
    max_duration: {max_duration}
    """
    )
    if (
        (snr < 20 or snr > 28)
        or duration > max_duration
        or text_similarity < 95
        or has_non_silence
    ):
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
    max_takes=10,
    speech_wpm=150,
    save_all_takes=False,
    output_dir=None,
    output_file_prefix=None,
):
    current_take = 0
    takes = []
    take_to_save = None
    while max_takes > 0:
        audio, is_bad, results = generate_speech(
            sentence, history_prompt, text_temp, waveform_temp, speech_wpm
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
            take_to_save = (audio, is_bad, results)
            break
        print(f"Doing another take... {max_takes} left")
        max_takes -= 1

    if take_to_save is None:
        # If we get here, find the best take and use that
        # Sorted by desc text_similarity, snr, then ascending duration
        sorted_takes = sorted(
            takes,
            key=lambda x: (x[2]["text_similarity"], x[2]["snr"], -x[2]["duration"]),
            reverse=True,
        )
        take_to_save = sorted_takes[0]
        print(f"Best take: {take_to_save[2]}")

    return take_to_save


def generate_long_sentence_as_takes(
    sentence,
    history_prompt,
    text_temp,
    waveform_temp,
    max_takes=10,
    speech_wpm=150,
    save_all_takes=False,
    output_dir=None,
    output_file_prefix=None,
):
    sentence_parts = nltk.sent_tokenize(sentence)

    silence = np.zeros(int(0.25 * NEW_SAMPLE_RATE))
    pieces = []
    for idx, part in enumerate(sentence_parts):
        best_take = generate_speech_as_takes(
            part,
            history_prompt,
            text_temp,
            waveform_temp,
            max_takes,
            speech_wpm,
            save_all_takes,
            output_dir,
            output_file_prefix + f"-{idx}",
        )

        pieces += [best_take[0], silence]

    return np.concatenate(pieces)


def save_audio_signal_wav(audio_signal, sample_rate, output_file):
    # Convert the audio signal to a 16-bit integer array
    int_audio_signal = (audio_signal * np.iinfo(np.int16).max).astype(np.int16)
    wavfile.write(output_file, sample_rate, int_audio_signal)
