#!usr/bin/env python

import glob
import os
import random
import re
import logging
import numpy as np
import cv2

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

from PIL import Image
from math import sqrt
from skimage.color import rgb2gray
from skimage.feature import ORB
from typing import Optional
from utils import utils, parsers

from .base import AICPBaseTool

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)


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

            # Get points of interest from image
            start_point, end_point = self.find_interest_points_by_thirds(img)

            # Zoom in/out flipper
            zoom_factor = zoom_factor * self.random_sign()
            if zoom_factor > 0:
                temp_point = start_point
                start_point = end_point
                end_point = temp_point

            print(f"ZOOM FACTOR: {zoom_factor}")

            cmd = self.generate_animation_ffmpeg_command(
                img, video_file, start_point, end_point, zoom_factor, duration
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

        if self.video.production_config.voiceline_synced_storyboard:
            # Use voiceline synced storyboard images
            vo_lines = parsers.get_voiceover_lines()
            for i, vo_line in enumerate(vo_lines, start=1):
                image = os.path.join(image_path, f"scene_{i:02}_01.png")
                images_dict[image] = vo_line.duration
        else:
            # use default storyboard images
            for i, scene in enumerate(scenes):
                scene_images = glob.glob(
                    os.path.join(utils.STORYBOARD_PATH, f"scene_{i+1:02}_*.png")
                )
                duration_per_image = scene.duration / len(scene_images)

                for img in scene_images:
                    image = os.path.join(image_path, os.path.basename(img))
                    images_dict[image] = duration_per_image

        return images_dict

    def find_interest_points_by_thirds(self, image_path):
        """
        Determine points of interest in an image and find the furthest third.

        Given an image path, this function uses the ORB method to detect keypoints
        and then determines the quadrant (consisting of four "ninths" based on the rule
        of thirds) that contains the most keypoints. It then calculates the center
        point of that quadrant and the center point of the furthest third based on
        the image's orientation.

        Parameters:
        - image_path (str): Path to the input image.

        Returns:
        - tuple: A tuple containing:
          - (int, int): Coordinates (x, y) of the center of the quadrant with the most keypoints.
          - (int, int): Coordinates (x, y) of the center of the furthest third.

        Note:
        The orientation of the image (portrait or landscape) affects the calculation
        of the rule of thirds and the determination of the furthest third. In landscape
        orientation, thirds are calculated from left to right, while in portrait
        orientation, they are calculated from top to bottom.
        """
        # Load the image
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        height, width = image.shape

        # Determine image orientation
        orientation = "portrait" if height > width else "landscape"

        # Calculate the rule of thirds grid
        vertical_third_length = height // 3
        horizontal_third_length = width // 3

        # Define the quadrants made up of four ninths
        quadrants = {
            "upper_left": [
                (0, 0, horizontal_third_length, vertical_third_length),
                (
                    0,
                    vertical_third_length,
                    horizontal_third_length,
                    vertical_third_length * 2,
                ),
                (
                    horizontal_third_length,
                    0,
                    horizontal_third_length * 2,
                    vertical_third_length,
                ),
                (
                    horizontal_third_length,
                    vertical_third_length,
                    horizontal_third_length * 2,
                    vertical_third_length * 2,
                ),
            ],
            "upper_right": [
                (
                    horizontal_third_length,
                    0,
                    horizontal_third_length * 2,
                    vertical_third_length,
                ),
                (
                    horizontal_third_length,
                    vertical_third_length,
                    horizontal_third_length * 2,
                    vertical_third_length * 2,
                ),
                (horizontal_third_length * 2, 0, width, vertical_third_length),
                (
                    horizontal_third_length * 2,
                    vertical_third_length,
                    width,
                    vertical_third_length * 2,
                ),
            ],
            "lower_left": [
                (
                    0,
                    vertical_third_length,
                    horizontal_third_length,
                    vertical_third_length * 2,
                ),
                (0, vertical_third_length * 2, horizontal_third_length, height),
                (
                    horizontal_third_length,
                    vertical_third_length,
                    horizontal_third_length * 2,
                    vertical_third_length * 2,
                ),
                (
                    horizontal_third_length,
                    vertical_third_length * 2,
                    horizontal_third_length * 2,
                    height,
                ),
            ],
            "lower_right": [
                (
                    horizontal_third_length,
                    vertical_third_length,
                    horizontal_third_length * 2,
                    vertical_third_length * 2,
                ),
                (
                    horizontal_third_length,
                    vertical_third_length * 2,
                    horizontal_third_length * 2,
                    height,
                ),
                (
                    horizontal_third_length * 2,
                    vertical_third_length,
                    width,
                    vertical_third_length * 2,
                ),
                (horizontal_third_length * 2, vertical_third_length * 2, width, height),
            ],
        }

        # Use ORB to detect keypoints
        orb = cv2.ORB_create()
        keypoints = orb.detect(image, None)

        # Count keypoints in each quadrant
        quadrant_keypoint_counts = {}
        for quadrant_name, boxes in quadrants.items():
            count = sum(
                [
                    1
                    for kp in keypoints
                    if any(
                        [
                            box[0] <= kp.pt[0] < box[2] and box[1] <= kp.pt[1] < box[3]
                            for box in boxes
                        ]
                    )
                ]
            )
            quadrant_keypoint_counts[quadrant_name] = count

        # Determine the quadrant of interest
        max_quadrant = max(quadrant_keypoint_counts, key=quadrant_keypoint_counts.get)

        # Calculate the center point of the quadrant of interest
        x1, y1, x2, y2 = (
            (quadrants[max_quadrant][0][0] + quadrants[max_quadrant][2][2]) // 2,
            (quadrants[max_quadrant][0][1] + quadrants[max_quadrant][2][3]) // 2,
            (quadrants[max_quadrant][1][0] + quadrants[max_quadrant][3][2]) // 2,
            (quadrants[max_quadrant][1][1] + quadrants[max_quadrant][3][3]) // 2,
        )
        quadrant_center_x = (x1 + x2) // 2
        quadrant_center_y = (y1 + y2) // 2

        # Find the center point of the furthest third
        if orientation == "landscape":
            if "left" in max_quadrant:
                furthest_third_x = horizontal_third_length * 5 // 2
            else:
                furthest_third_x = horizontal_third_length // 2
            furthest_third_y = height // 2
        else:  # portrait
            if "upper" in max_quadrant:
                furthest_third_y = vertical_third_length * 5 // 2
            else:
                furthest_third_y = vertical_third_length // 2
            furthest_third_x = width // 2

        return (quadrant_center_x, quadrant_center_y), (
            furthest_third_x,
            furthest_third_y,
        )

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

        zoom_start = 1.001

        # zoom out
        if zoom_factor < 0:
            # padding for the initial zoom
            zoom_padding = round(abs(zoom_factor) * (duration * fps), 3)
            if zoom_padding > 1:
                zoom_padding = round(zoom_padding - 0.700, 3)
            print(f"{input_image_path}, zoom start: {zoom_start}, zoom padding: {zoom_padding}")
            command = (
                f"ffmpeg -loop 1 -i {input_image_path} -vf "
                f"\"zoompan=z='if(lte(zoom,1.0),zoom+{zoom_padding},max({zoom_start},zoom+{zoom_factor}))':x='x+{x_movement}':y='y+{y_movement}':d={duration*fps}\" "
                f"-c:v libx264 -preset ultrafast -r {fps} -s {width}x{height} -pix_fmt yuv420p -t {duration} -probesize 42M {output_video_path}"
            )
        # zoom in
        else:
            command = (
                f"ffmpeg -loop 1 -i {input_image_path} -vf "
                f"\"zoompan=z='min(zoom+{zoom_factor},zoom+{zoom_start})':x='x+{x_movement}':y='y+{y_movement}':d={duration*fps}\" "
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
        video_files = self._sorted(glob.glob(f"{video_dir}/scene_*_*.mp4"))

        video_list = os.path.join(utils.PATH_PREFIX, "concat.txt")
        with open(video_list, "w") as f:
            for video_file in video_files:
                file = video_file.replace(f"{utils.PATH_PREFIX}/", "")
                f.write(f"file '{file}'\n")

        command = f"ffmpeg -f concat -safe 0 -i {video_list} -c copy {output_file}"
        return command

    def _sorted(self, filepaths):
        def key_func(filepath):
            match = re.match(r"scene_(\d+)_(\d+).mp4", os.path.basename(filepath))
            if match:
                n, t = map(int, match.groups())
                return n, t
            return 0, 0

        return sorted(filepaths, key=key_func)

    def random_sign(self):
        """
        This function does a "coin flip" and returns 1 or -1
        """
        return random.choice([-1, 1])
