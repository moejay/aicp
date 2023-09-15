"""Module containing ffmpeg functions."""

import os
import subprocess
import json

def get_video_info(video_path: str) -> dict:
    """Get information about a video file."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            video_path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)

def concatenate_clips(
    clips: list[str], output_path: str
) -> None:
    """Concatenate clips into a single video file."""
    # Create a file with the list of clips to concatenate
    concat_file_path = "concat.txt"
    with open(concat_file_path, "w") as f:
        for clip in clips:
            new_clip = clip
            # If clip doesn't have audio, then add a silent audio track
            if len(get_video_info(clip)["streams"]) == 1:
                new_clip = clip + "_with_silence.mp4"
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-f",
                        "lavfi",
                        "-i",
                        "anullsrc=channel_layout=stereo:sample_rate=44100",
                        "-i",
                        clip,
                        "-shortest",
                        "-c:v",
                        "copy",
                        "-c:a",
                        "aac",
                        "-b:a",
                        "192k",
                        new_clip,
                    ], check=True
                )
            f.write(f"file '{new_clip}'\n")
    # Concatenate the clips
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_file_path,
            "-c:v",
            "libx264",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            output_path,
        ], check=True,
    )
    # Remove the file with the list of clips to concatenate
    os.remove(concat_file_path)


def create_video_from_image(
    image_path: str, output_path: str, duration: float = 5.0
) -> None:
    """Create a video from an image."""
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            image_path,
            "-c:v",
            "libx264",
            "-t",
            str(duration),
            "-pix_fmt",
            "yuv420p",
            output_path,
        ], check=True
    )

def combine_audio_and_video(
    audio_path: str, video_path: str, output_path: str
) -> None:
    """Combine audio and video files into a single video file."""
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-i",
            audio_path,
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-strict",
            "experimental",
            output_path,
        ], check=True
    )

def overlay_video_on_video(
    video_path: str, overlay_path: str, output_path: str
) -> None:
    """Overlay a video on top of another video."""
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-i",
            overlay_path,
            "-filter_complex",
            "[0:v][1:v]overlay=0:0",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "copy",
            output_path,
        ], check=True
    )

def mix_wav_files(input_files, output_file):
    if len(input_files) == 0:
        raise ValueError("No input files provided.")

    input_str = "".join(["-i " + file + " " for file in input_files])
    filter_complex_str = f"amix=inputs={len(input_files)}:duration=longest:dropout_transition=3"

    command = (
        f"ffmpeg -y {input_str} -filter_complex \"{filter_complex_str}\" {output_file}"
    )

    subprocess.run(command, shell=True, check=True)

