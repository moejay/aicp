import subprocess
import sys
import torch as th
import torchaudio as ta

from dora.log import fatal
from demucs.apply import apply_model
from demucs.audio import AudioFile, convert_audio
from demucs.pretrained import get_model_from_args
from demucs.repo import ModelLoadingError


def load_track(track, audio_channels, samplerate):
    errors = {}
    wav = None

    try:
        wav = AudioFile(track).read(
            streams=0, samplerate=samplerate, channels=audio_channels
        )
    except FileNotFoundError:
        errors["ffmpeg"] = "FFmpeg is not installed."
    except subprocess.CalledProcessError:
        errors["ffmpeg"] = "FFmpeg could not read the file."

    if wav is None:
        try:
            wav, sr = ta.load(str(track))
        except RuntimeError as err:
            errors["torchaudio"] = err.args[0]
        else:
            wav = convert_audio(wav, sr, samplerate, audio_channels)

    if wav is None:
        print(
            f"Could not load file {track}. " "Maybe it is not a supported file format? "
        )
        for backend, error in errors.items():
            print(
                f"When trying to load using {backend}, got the following error: {error}"
            )
        sys.exit(1)
    return wav


def separate_sources(
    track_path,
    model_name="demucs",
    device="cuda" if th.cuda.is_available() else "cpu",
    shifts=1,
    split=True,
    overlap=0.25,
    stem=None,
):
    """
    Separate the sources of a given audio track.

    Parameters:
    - track_path (str): Path to the audio track.
    - model_name (str): Name of the pre-trained model to use.
    - device (str): Device to use ('cpu' or 'cuda').
    - shifts (int): Number of random shifts for stabilization.
    - split (bool): Split audio in chunks or not.
    - overlap (float): Overlap between splits.
    - segment (int): Size of each chunk.
    - stem (str): Separate audio into specific stem and no_stem.

    Returns:
    - dict: A dictionary where keys are source names and values are separated audio data.
    """

    class ModelArgs:
        def __init__(self, name, device):
            self.name = None
            self.device = device
            self.repo = None

    args = ModelArgs(model_name, device)
    # Load pre-trained model
    try:
        model = get_model_from_args(args)
    except ModelLoadingError as error:
        fatal(error.args[0])

    # Load and preprocess audio
    wav = load_track(track_path, model.audio_channels, model.samplerate)
    ref = wav.mean(0)
    wav -= ref.mean()
    wav /= ref.std()

    # Apply model to separate sources
    sources = apply_model(
        model,
        wav[None],
        device=device,
        shifts=shifts,
        split=split,
        overlap=overlap,
        num_workers=0,
    )[0]

    # Post-process separated sources
    sources *= ref.std()
    sources += ref.mean()

    # Convert sources to dictionary format
    sources_dict = {}
    if stem is None:
        for source, name in zip(sources, model.sources):
            sources_dict[name] = source
    else:
        sources_dict[stem] = sources[model.sources.index(stem)]
        other_stem = th.zeros_like(sources[0])
        for i in sources:
            other_stem += i
        sources_dict["no_" + stem] = other_stem

    return sources_dict


def demucs_voice_filter(filepath):
    """
    Separate the voice from a given audio track and return the filtered track.
    """
    sources = separate_sources(filepath)
    return sources["vocals"][0]
