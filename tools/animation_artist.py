#!usr/bin/env python

import glob
import os
import random
import yaml
import logging
import matplotlib.image as mpimg
import matplotlib.patches as patches
import numpy as np

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

from PIL import Image
from math import sqrt
from skimage.color import rgb2gray
from skimage.feature import ORB
from typing import Optional
from utils import llms, utils, parsers

from .base import AICPBaseTool

logger = logging.getLogger(__name__)


class AnimationArtistTool(AICPBaseTool):
    name = "animationartist"
    description = "Useful when you need to turn still images into videos"

    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        if self.video.director.get_animation_artist() == None:
            return "Skipping animation artist"

        # Load artist configuration
        cast_member = self.video.director.get_animation_artist()
        roi_box1 = cast_member.roi_box1
        roi_box2 = cast_member.roi_box2
        zoom_factor = cast_member.zoom_factor
        fps = cast_member.fps

        scenes = parsers.get_scenes()
        images = self.get_scene_images(scenes)

        # animate images
        for img in images.keys():
            print(f"Animating storyboard image: {img}")
            duration = images[img]
            video_file = img.replace("png", "mp4")

            # Skip if video file already exists
            if os.path.exists(video_file):
                continue

            # Zoom in/out randomness
            zoom_factor = zoom_factor * self.random_sign()
            print(f"ZOOM FACTOR: {zoom_factor}")

            box1, box2 = self.find_regions_of_interest(img, roi_box1, roi_box2)
            cmd = self.generate_animation_ffmpeg_command(
                img, video_file, box1, box2, zoom_factor, duration
            )
            os.system(cmd)

        # concat animations
        cmd = self.generate_concat_ffmpeg_command(
            os.path.dirname(list(images.keys())[0]), utils.ANIMATION_VIDEO_FILE
        )
        os.system(cmd)

        return "Done generating animation"

    def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")

    def get_scene_images(self, scenes):
        images_dict = {}

        image_path = utils.STORYBOARD_PATH

        if os.path.exists(os.path.join(utils.STORYBOARD_PATH, "img2img")):
            # use img2img upscaled images if they exist
            image_path = os.path.join(utils.STORYBOARD_PATH, "img2img")

        for i, scene in enumerate(scenes):
            scene_images = glob.glob(
                os.path.join(utils.STORYBOARD_PATH, f"scene_{i+1}_*.png")
            )
            duration_per_image = scene.duration / len(scene_images)

            for img in scene_images:
                image = os.path.join(image_path, os.path.basename(img))
                images_dict[image] = duration_per_image

        return images_dict

    def find_regions_of_interest(self, image_path, box1, box2):
        # Open the image file
        img = Image.open(image_path)

        # Convert the image to grayscale
        img_gray = rgb2gray(np.array(img))

        # Get image dimensions
        img_height, img_width = img_gray.shape

        # Initialize ORB detector
        orb = ORB(n_keypoints=200)

        # Detect keypoints in the image
        orb.detect_and_extract(img_gray)

        # Extract coordinates of detected keypoints
        keypoints = orb.keypoints

        # Initialize an empty array to count keypoints
        keypoint_counts_box1 = np.zeros((img_height - box1 + 1, img_width - box1 + 1))
        keypoint_counts_box2 = np.zeros((img_height - box2 + 1, img_width - box2 + 1))

        # Count keypoints in each window
        for y, x in keypoints:
            for i in range(
                max(0, int(y) - box1 + 1), min(int(y) + 1, img_height - box1 + 1)
            ):
                for j in range(
                    max(0, int(x) - box1 + 1), min(int(x) + 1, img_width - box1 + 1)
                ):
                    keypoint_counts_box1[i, j] += 1

            for i in range(
                max(0, int(y) - box2 + 1), min(int(y) + 1, img_height - box2 + 1)
            ):
                for j in range(
                    max(0, int(x) - box2 + 1), min(int(x) + 1, img_width - box2 + 1)
                ):
                    keypoint_counts_box2[i, j] += 1

        # Find the window with the highest concentration of keypoints
        max_keypoints_y_box1, max_keypoints_x_box1 = np.unravel_index(
            keypoint_counts_box1.argmax(), keypoint_counts_box1.shape
        )

        # Calculate the window's pixel coordinates
        window_top_box1 = max_keypoints_y_box1
        window_left_box1 = max_keypoints_x_box1
        window_bottom_box1 = max_keypoints_y_box1 + box1
        window_right_box1 = max_keypoints_x_box1 + box1

        # Remove the overlapping region in the keypoint_counts_box2
        keypoint_counts_box2[
            max(0, window_top_box1 - box2) : min(
                img_height - box2 + 1, window_bottom_box1
            ),
            max(0, window_left_box1 - box2) : min(
                img_width - box2 + 1, window_right_box1
            ),
        ] = 0

        # Find the window with the highest concentration of keypoints in the updated keypoint_counts_box2
        max_keypoints_y_box2, max_keypoints_x_box2 = np.unravel_index(
            keypoint_counts_box2.argmax(), keypoint_counts_box2.shape
        )

        # Calculate the window's pixel coordinates
        window_top_box2 = max_keypoints_y_box2
        window_left_box2 = max_keypoints_x_box2
        window_bottom_box2 = max_keypoints_y_box2 + box2
        window_right_box2 = max_keypoints_x_box2 + box2

        # Calculate the center points of the regions
        center_box1 = (
            (window_left_box1 + window_right_box1) // 2,
            (window_top_box1 + window_bottom_box1) // 2,
        )
        center_box2 = (
            (window_left_box2 + window_right_box2) // 2,
            (window_top_box2 + window_bottom_box2) // 2,
        )

        return center_box1, center_box2

    def generate_animation_ffmpeg_command(
        self,
        input_image_path,
        output_video_path,
        start_coordinates,
        end_coordinates,
        zoom_factor=0.0030,
        duration=3,
        fps=60,
    ):
        """
        This function generates an ffmpeg command to create a video with camera movement from point A to point B.
        Parameters:
        input_image_path (str): The path to the input image.
        output_video_path (str): The path to the output video.
        start_coordinates (tuple): The starting coordinates (x, y).
        end_coordinates (tuple): The ending coordinates (x, y).
        zoom_factor (float): The zoom factor. Positive values zoom in, negative values zoom out.
        duration (int): The duration of the video in seconds.
        fps (int): The frames per second of the output video.

        Returns:
        str: The ffmpeg command.
        """
        # get the resolution of the input image
        with Image.open(input_image_path) as img:
            width, height = img.size

        # extract start and end coordinates
        start_x, start_y = start_coordinates
        end_x, end_y = end_coordinates

        # calculate x and y movements
        x_movement = (end_x - start_x) / (duration * fps)
        y_movement = (end_y - start_y) / (duration * fps)

        # get the aspect ratio of the image
        if width > height:
            aspect_ratio = width / height
        else:
            aspect_ratio = height / width

        # zoom out
        if zoom_factor < 0:
            # try to understand how much movement is to happen for this clip
            movement_factor = sqrt((end_x - start_x) ** 2 + (end_y - start_y) ** 2) / (
                fps * duration
            )

            # reduce factor for long movements
            if movement_factor > 1.0:
                movement_factor = movement_factor / aspect_ratio

            # initial zoom padding when zooming out
            zoom_padding = (abs(zoom_factor) * movement_factor) * (fps * duration)

            print(f"{input_image_path} zoom padding: {zoom_padding}")
            command = (
                f"ffmpeg -loop 1 -i {input_image_path} -vf "
                f"\"zoompan=z='if(eq(zoom,1.0),zoom+{zoom_padding},zoom+{zoom_factor})':x='x+{x_movement}':y='y+{y_movement}':d={duration*fps}\" "
                f"-c:v libx264 -preset ultrafast -r {fps} -s {width}x{height} -pix_fmt yuv420p -t {duration} -probesize 42M {output_video_path}"
            )
        # zoom in
        else:
            zoom_padding = 0.01
            command = (
                f"ffmpeg -loop 1 -i {input_image_path} -vf "
                f"\"zoompan=z='min(zoom+{zoom_factor},zoom+{zoom_padding})':x='x+{x_movement}':y='y+{y_movement}':d={duration*fps}\" "
                f"-c:v libx264 -preset ultrafast -r {fps} -s {width}x{height} -pix_fmt yuv420p -t {duration} -probesize 42M {output_video_path}"
            )

        return command

    def generate_concat_ffmpeg_command(self, video_dir, output_file):
        """
        This function generates an ffmpeg command to concatenate all video files in a directory.

        Parameters:
        video_dir (str): The path to the directory containing the video files.
        output_file (str): The path to the output file.

        Returns:
        str: The ffmpeg command.
        """

        # get list of all video filenames in the directory
        video_files = glob.glob(f"{video_dir}/*.mp4")
        video_files = sorted(video_files)

        video_list = os.path.join(utils.PATH_PREFIX, "concat.txt")
        with open(video_list, "w") as f:
            for video_file in video_files:
                file = video_file.replace(f"{utils.PATH_PREFIX}/", "")
                f.write(f"file '{file}'\n")

        command = f"ffmpeg -f concat -safe 0 -i {video_list} -c copy {output_file}"
        return command

    def random_sign(self):
        """
        This function does a "coin flip" and returns 1 or -1
        """
        return random.choice([-1, 1])
