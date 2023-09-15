import json
import os
from backend.models import AICPClip, AICPLayer, AICPMusicLayer, AICPOutline, AICPScene, AICPSequence, AICPShot, AICPVideoLayer, AICPVoiceoverLayer
from generators.image import ImageGenerator
from generators.voiceover import VoiceoverGenerator
from backend.utils import ffmpeg, audio_utils


image_generator = ImageGenerator()
voiceover_generator = VoiceoverGenerator()

def save_layer_parameters_to_file(params: dict, layer_id: str, output_dir: str) -> None:
    """Save the layer parameters to a file."""
    with open(output_dir + layer_id + ".json", "w") as f:
        f.write(json.dumps(params))

def load_layer_parameters_from_file(layer_id: str, output_dir: str) -> dict:
    """Load the layer parameters from a file."""
    if not os.path.exists(output_dir + layer_id + ".json"):
        return {}
    with open(output_dir + layer_id + ".json", "r") as f:
        return json.loads(f.read())
    
def compare_layer_parameters(params1: dict, params2: dict) -> bool:
    """Compare two sets of layer parameters."""
    return params1 == params2

def unload_all_generators():
    """Unload all generators."""
    image_generator.unload_model()
    voiceover_generator.unload_model()

def render_video_layer(layer: AICPVideoLayer, output_dir: str) -> str:
    """Render the video layer."""
    output_path = os.path.join(output_dir, layer.id + ".mp4")
    layer_params_dict = {
        "prompt": layer.prompt,
        "positive_prompt": layer.positive_prompt,
        "negative_prompt": layer.negative_prompt,
        "model": layer.model,
        "seed": layer.seed,
        "width": layer.width,
        "height": layer.height,
        "duration": layer.duration,
    }
    existing_params = load_layer_parameters_from_file(layer.id, output_dir)
    if compare_layer_parameters(layer_params_dict, existing_params):
        return output_path

    unload_all_generators()
    image_generator.load_model(model=layer.model)
    # Compare without duration
    existing_params.get("duration", None)
    new_duration = layer.duration
    existing_params.pop("duration", None)
    layer_params_dict.pop("duration", None)
    image_path =os.path.join(output_dir , layer.id + ".png")
    if not compare_layer_parameters(layer_params_dict, existing_params):
        # If the parameters are different, we need to regenerate the image 
        image_generator.generate(
            prompt=layer.prompt + layer.positive_prompt,
            negative_prompt=layer.negative_prompt,
            width=layer.width,
            height=layer.height,
            output_path=image_path,
        )
    ffmpeg.create_video_from_image(image_path, output_path, layer.duration)
    layer_params_dict["duration"] = new_duration
    save_layer_parameters_to_file(layer_params_dict, layer.id, output_dir)
    return output_path

def render_voiceover_layer(layer: AICPVoiceoverLayer, output_dir: str) -> str:
    """Render the voiceover layer."""
    output_path = os.path.join(output_dir, layer.id + ".wav")
    layer_params_dict = {
        "prompt": layer.prompt,
        "speaker": layer.speaker,
        "speaker_text_temp": layer.speaker_text_temp,
        "speaker_waveform_temp": layer.speaker_waveform_temp,
    }
    existing_params = load_layer_parameters_from_file(layer.id, output_dir)
    if compare_layer_parameters(layer_params_dict, existing_params):
        return output_path

    unload_all_generators()
    voiceover_generator.load_model()
    voiceover_generator.generate(
        prompt=layer.prompt,
        speaker=layer.speaker,
        speaker_text_temp=layer.speaker_text_temp,
        speaker_waveform_temp=layer.speaker_waveform_temp,
        output_path=output_path,
    )
    save_layer_parameters_to_file(layer_params_dict, layer.id, output_dir)
    return output_path

def render_music_layer(layer: AICPMusicLayer, output_dir: str) -> str:
    """Render the music layer."""



def render_layer(layer: AICPLayer, output_dir: str) -> str:
    """Render the layer."""
    if isinstance(layer, AICPVoiceoverLayer):
        return render_voiceover_layer(layer, output_dir)
    elif isinstance(layer, AICPVideoLayer):
        return render_video_layer(layer, output_dir)
    elif isinstance(layer, AICPMusicLayer):
        return render_music_layer(layer, output_dir)
    else:
        raise ValueError(f"Unknown layer type: {type(layer)}")
    
def render_and_mix_layers(layers: list[AICPLayer], output_path: str, default_duration: float = 1.0) -> str:
    """Render the layers."""
    # Determine the duration of the clip, if possible
    # by looking at the duration of the all the layers
    # If any of the layers have durations, find the max and use it
    # If none of the layers have durations, then render voiceover layers first
    # And find it's generated duration and use that
    # If there are no voiceover layers, then use a default duration of 1 second

    output_dir = os.path.dirname(output_path)
    max_duration = 0.0
    for layer in layers:
        if layer.duration:
            max_duration = max(max_duration, layer.duration)

    if max_duration == 0.0:
        # Render voiceover layers first
        for layer in layers:
            if isinstance(layer, AICPVoiceoverLayer):
                vo_layer_path = render_layer(layer, output_dir)
                vo_layer_duration = audio_utils.get_audio_file_length(vo_layer_path)
                max_duration = max(max_duration, vo_layer_duration)

    if max_duration == 0.0:
        max_duration = default_duration
    
    for layer in layers:
        if not layer.duration:
            layer.duration = max_duration
        render_layer(layer, output_dir)
    
    # Get all layers of type audio
    audio_layers = [layer for layer in layers if isinstance(layer, AICPVoiceoverLayer) or isinstance(layer, AICPMusicLayer)]
    # Get all layers of type video
    video_layers = [layer for layer in layers if isinstance(layer, AICPVideoLayer)]
    # Mix the audio layers
    audio_utils.mix_audio_files(
        [render_layer(layer, output_dir) for layer in audio_layers],
        os.path.join(output_dir, "audio.wav"),
    )
    # Combine the video layers
    ffmpeg.combine_audio_and_video(
        os.path.join(output_dir, "audio.wav"),
        render_layer(video_layers[0], output_dir),
        output_path,
    )

    if len(video_layers) > 1:
        for layer in video_layers[1:]:
            ffmpeg.overlay_video_on_video(
                output_path,
                render_layer(layer, output_dir),
                output_path,
            )

    return output_path




def combine_clips(clips: list[str], output_path: str) -> str:
    """Combine the clips."""
    ffmpeg.concatenate_clips(clips, output_path)
    return output_path
    
def render_shot(shot: AICPShot, output_dir: str) -> str:
    """Render the shot."""
    return render_and_mix_layers(shot.layers, os.path.join(output_dir , shot.id + ".mp4"))

def render_scene(scene: AICPScene, output_dir: str) -> str:
    """Render the scene."""
    shot_paths = []
    for shot in scene.shots:
        shot_dir = os.path.join(output_dir, "shots", shot.id)
        os.makedirs(shot_dir, exist_ok=True)
        shot_paths.append(render_shot(shot, shot_dir))
    return combine_clips(shot_paths, os.path.join(output_dir, "scene.mp4"))

def render_sequence(sequence: AICPSequence, output_dir: str) -> str:
    """Render the sequence."""
    scene_paths = []
    for scene in sequence.scenes:
        scene_dir = os.path.join(output_dir, "scenes", scene.id)
        os.makedirs(scene_dir, exist_ok=True)
        scene_paths.append(render_scene(scene, scene_dir))

    return combine_clips(scene_paths, os.path.join(output_dir, "sequence.mp4"))
    

def render_outline(outline: AICPOutline, output_dir: str) -> str:
    """Render the outline."""
    sequence_paths = []
    for sequence in outline.sequences:
        sequence_dir = os.path.join(output_dir, "sequences", sequence.id)
        os.makedirs(sequence_dir, exist_ok=True)
        sequence_paths.append(render_sequence(sequence, sequence_dir))

    return combine_clips(sequence_paths, os.path.join(output_dir, "outline.mp4"))
