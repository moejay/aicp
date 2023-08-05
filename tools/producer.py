#!/usr/bin/env python

import glob
import os
import subprocess

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from typing import Optional
from utils import utils, parsers
from .base import AICPBaseTool


class ProducerTool(AICPBaseTool):
    name = "producer"
    description = "Useful when you want to finalize the video file"

    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        scenes = parsers.get_scenes()
        audio_dict = {utils.FINAL_AUDIO_FILE: 0}

        # Create video from animated images
        if os.path.exists(utils.ANIMATION_VIDEO_FILE):
            self.combine_audio_with_video(
                audio_dict, utils.ANIMATION_VIDEO_FILE, utils.FINAL_VIDEO_FILE
            )
        # Create video from still images
        else:
            images = self.get_scene_images(scenes)

            resolution = (
                self.video.production_config.video_width,
                self.video.production_config.video_height,
            )
            output_file = utils.FINAL_VIDEO_FILE
            self.create_video_from_images_with_audio(
                images, audio_dict, resolution, output_file
            )

        # Add subtitles
        self._add_subtitles()

        return "Done producing video file"

    def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")

    def get_scene_images(self, scenes):
        images_dict = {}

        if os.path.exists(os.path.join(utils.STORYBOARD_PATH, "restored_imgs")):
            # use gfpgan upscaled images if they exist
            upscaler_path = "restored_imgs"
        else:
            upscaler_path = ""

        for i, scene in enumerate(scenes):
            scene_images = glob.glob(
                os.path.join(utils.STORYBOARD_PATH, f"scene_{i+1}_*.png")
            )
            duration_per_image = scene.duration / len(scene_images)

            for img in scene_images:
                image = os.path.join(upscaler_path, os.path.basename(img))
                images_dict[image] = duration_per_image

        return images_dict

    def _add_subtitles(self):
        if not self.video.production_config.enable_subtitles:
            return
        if not os.path.exists(utils.VOICEOVER_SUBTITLES):
            return

        input_file = utils.FINAL_VIDEO_FILE
        output_file = utils.FINAL_VIDEO_FILE
        subtitle_file = utils.VOICEOVER_SUBTITLES

        text_color = "#FF0000"
        outline_color = "#0000000"
        back_color = "#000000"

        commands = generate_ffmpeg_commands(
            input_file,
            subtitle_file,
            output_file,
            [
                (
                    None,
                    None,
                ),
            ],
        )
        for command in commands:
            subprocess.run(command, shell=True)

    def combine_audio_with_video(self, audio_dict, input_file, output_file):
        # Add audio to the video
        sorted_audio = audio_dict.items()
        audio_input_str = ""
        audio_filter_str = ""
        for idx, (audio_path, start_time) in enumerate(sorted_audio, 1):
            audio_input_str += f"-i '{audio_path}' "
            audio_filter_str += f"[{idx}:a]adelay={int(start_time * 1000)}|{int(start_time * 1000)}[a{idx}];"

        # Concatenate audio streams
        audio_streams_str = "".join(
            f"[a{idx}]" for idx in range(1, len(sorted_audio) + 1)
        )
        audio_filter_str += f"{audio_streams_str}amix=inputs={len(sorted_audio)}[a]"

        # Construct the ffmpeg command for audio addition
        ffmpeg_cmd = f"ffmpeg -y -i {input_file} {audio_input_str}-filter_complex '{audio_filter_str}' -map 0:v -map '[a]' -c:v copy '{output_file}'"
        subprocess.run(ffmpeg_cmd, shell=True)

    def create_video_from_images_with_audio(
        self, images_dict, audio_dict, resolution, output_file
    ):
        # Create video from images
        sorted_images = images_dict.items()

        # Create a temporary file with the list of images and durations
        if os.path.exists(os.path.join(utils.STORYBOARD_PATH, "restored_imgs")):
            # use gfpgan upscaled images if they exist
            image_set = "restored_imgs"
        elif os.path.exists(os.path.join(utils.STORYBOARD_PATH, "img2img")):
            # use img2img upscaled images if they exist
            image_set = "img2img"
        else:
            image_set = ""

        print(f"IMAGE_SET={image_set}")
        images_list_file = os.path.join(utils.STORYBOARD_PATH, "images_list.txt")

        with open(images_list_file, "w") as f:
            for image_path, duration in sorted_images:
                f.write(f"file '{image_set}/{image_path}'\n")
                f.write(f"duration {duration}\n")

        # Construct the ffmpeg command for video creation
        scale_filter = f"scale=w={resolution[0]}:h={resolution[1]}:force_original_aspect_ratio=1,pad={resolution[0]}:{resolution[1]}:(ow-iw)/2:(oh-ih)/2"
        # Audio compressor
        audio_compressor = '-filter:a "speechnorm=e=6.75:r=0.00001:l=1"'
        # codec
        codec = "-c:v libx264 -preset ultrafast"

        ffmpeg_cmd = f"ffmpeg -y -f concat -i {images_list_file} -vf '{scale_filter}' -r 30 {audio_compressor} {codec} -y '{utils.TEMP_VIDEO_FILE}'"
        subprocess.run(ffmpeg_cmd, shell=True)

        # Add audio to the video
        sorted_audio = audio_dict.items()
        audio_input_str = ""
        audio_filter_str = ""
        for idx, (audio_path, start_time) in enumerate(sorted_audio, 1):
            audio_input_str += f"-i '{audio_path}' "
            audio_filter_str += f"[{idx}:a]adelay={int(start_time * 1000)}|{int(start_time * 1000)}[a{idx}];"

        # Concatenate audio streams
        audio_streams_str = "".join(
            f"[a{idx}]" for idx in range(1, len(sorted_audio) + 1)
        )
        audio_filter_str += f"{audio_streams_str}amix=inputs={len(sorted_audio)}[a]"

        # Construct the ffmpeg command for audio addition
        ffmpeg_cmd = f"ffmpeg -y -i {utils.TEMP_VIDEO_FILE} {audio_input_str}-filter_complex '{audio_filter_str}' -map 0:v -map '[a]' -c:v copy '{output_file}'"
        subprocess.run(ffmpeg_cmd, shell=True)


def generate_ffmpeg_commands(input_file, subtitle_file, output_file, settings):
    commands = []
    # Split the video into parts according to the settings
    for i, setting in enumerate(settings):
        start_time = setting[0]
        end_time = settings[i + 1][0] if i + 1 < len(settings) else None
        # Generate the FFmpeg command for this part
        command = generate_ffmpeg_command(
            input_file,
            subtitle_file,
            start_time,
            end_time,
            os.path.join(utils.PATH_PREFIX, f"part{i}.mp4"),
        )
        commands.append(command)
    # Concatenate the parts back together
    concat_command = (
        f"ffmpeg -y -i 'concat:"
        + "|".join(
            os.path.join(utils.PATH_PREFIX, f"part{i}.mp4")
            for i in range(len(settings))
        )
        + f"' -c copy {output_file}"
    )
    commands.append(concat_command)
    return commands


def generate_ffmpeg_command(
    input_file, subtitle_file, start_time, end_time, output_file
):
    # Generate the FFmpeg command
    command = f"ffmpeg -y -i {input_file} -vf 'ass={subtitle_file}'"
    # Add the start and end times if provided
    if start_time is not None:
        command += f" -ss {start_time}"
    if end_time is not None:
        command += f" -to {end_time}"
    command += f" -c:v libx264 -preset ultrafast {output_file}"
    return command
