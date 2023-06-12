#!/usr/bin/env python

from typing import Optional, Type
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool
import subprocess
import wave
import contextlib

def create_video_with_audio(images_dict, audio_dict, resolution, output_file):
    # Create video from images
    temp_video_file = "temp_video.mp4"
    sorted_images = images_dict.items()

    # Create a temporary file with the list of images and durations
    with open('images_list.txt', 'w') as f:
        for image_path, duration in sorted_images:
            f.write(f"file '{image_path}'\n")
            f.write(f"duration {duration}\n")

    # Construct the ffmpeg command for video creation
    scale_filter = f"scale=w={resolution[0]}:h={resolution[1]}:force_original_aspect_ratio=1,pad={resolution[0]}:{resolution[1]}:(ow-iw)/2:(oh-ih)/2"
    ffmpeg_cmd = f"ffmpeg -f concat -i images_list.txt -vf '{scale_filter}' -r 30 -y '{temp_video_file}'"
    subprocess.run(ffmpeg_cmd, shell=True)

    # Add audio to the video
    sorted_audio = audio_dict.items()
    audio_input_str = ""
    audio_filter_str = ""
    for idx, (audio_path, start_time) in enumerate(sorted_audio, 1):
        audio_input_str += f"-i '{audio_path}' "
        audio_filter_str += f"[{idx}:a]adelay={int(start_time * 1000)}|{int(start_time * 1000)}[a{idx}];"

    # Concatenate audio streams
    audio_streams_str = "".join(f"[a{idx}]" for idx in range(1, len(sorted_audio) + 1))
    audio_filter_str += f"{audio_streams_str}amix=inputs={len(sorted_audio)}[a]"

    # Construct the ffmpeg command for audio addition
    ffmpeg_cmd = f"ffmpeg -i {temp_video_file} {audio_input_str}-filter_complex '{audio_filter_str}' -map 0:v -map '[a]' -c:v copy -y '{output_file}'"
    subprocess.run(ffmpeg_cmd, shell=True)

class ProducerTool(BaseTool):
    name = "producer"
    description = "Useful when you want to finalize the video file"

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        # Determine the video length
        # Will add 4 seconds to the audio script length for now, as a naive approach
        fname = 'script.wav'
        with contextlib.closing(wave.open(fname,'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
        video_duration = int(duration) + 4
        
        scene_timecodes = open("script_timecodes.txt", "r").readlines()
        images_dict = {}
        for idx, tc in enumerate(scene_timecodes):
            tc = tc.strip()
            if idx + 1 < len(scene_timecodes):
                images_dict[f"scene_{idx + 1}.png"] = float(scene_timecodes[idx + 1].strip()) - float(tc)
            else:
                images_dict[f"scene_{idx + 1}.png"] = video_duration - float(tc)

        audio_dict = {
                "script.wav": 0
        }

        resolution = (1920, 1080)
        output_file = "output.mp4"
        create_video_with_audio(images_dict, audio_dict, resolution, output_file)
        return "Done producing video file"

    def _arun(self, query:str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")
