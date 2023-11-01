#!usr/bin/env python

import json
import os
from pathlib import Path
import torch
import yaml
import logging

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from typing import Optional
from utils import llms, utils, parsers
from .base import AICPBaseTool

from animatediff import cli

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

camera_motion_to_lora_map = {
            "PanLeft": "models/motion_lora/v2_lora_PanLeft.ckpt",
            "PanRight": "models/motion_lora/v2_lora_PanRight.ckpt",
            "RollingAnticlockwise": "models/motion_lora/v2_lora_RollingAnticlockwise.ckpt",
            "RollingClockwise": "models/motion_lora/v2_lora_RollingClockwise.ckpt",
            "ZoomIn": "models/motion_lora/v2_lora_ZoomIn.ckpt",
            "ZoomOut": "models/motion_lora/v2_lora_ZoomOut.ckpt",
            "TiltUp": "models/motion_lora/v2_lora_TiltUp.ckpt",
            "TiltDown": "models/motion_lora/v2_lora_TiltDown.ckpt",
        }


class SDAnimatorArtist(AICPBaseTool):
    name = "sdanimatorartist"
    description = "Useful when you need to generate images for the script"

    scene_prompts = []
    positive_prompt = ""
    negative_prompt = ""
    clip_file = "final.mp4" # We will change this to preview.mp4 if config.preview is true

    def initialize_agent(self):
        self.load_prompts()

    def load_prompts(self):
        # load additive prompts
        cast_member = self.video.director.get_storyboard_artist()
        self.positive_prompt = cast_member.positive_prompt
        self.negative_prompt = cast_member.negative_prompt

        # load storyboard artist prompts if they exist or create them
        prompts_file = os.path.join(utils.PATH_PREFIX, "storyboard_prompts.yaml")
        if os.path.exists(prompts_file):
            with open(prompts_file) as prompts:
                logger.info("Loading existing prompts from: storyboard_prompts.yaml")
                self.scene_prompts = yaml.load(
                    prompts.read().strip(), Loader=yaml.Loader
                )
        else:
            logger.info("Generating text-to-image prompts for storyboard artist...")
            self.scene_prompts = self.ego()

    def ego(self):
        """Run the script through the mind of the storyboard artist
        to generate more descriptive prompts"""
        cast_member = self.video.director.get_storyboard_artist()
        prompt_params = parsers.get_params_from_prompt(cast_member.prompt)
        # This is in addition to the input (Human param)
        # Resolve params from existing config/director/program
        params = {}
        for param in prompt_params:
            params[param] = parsers.resolve_param_from_video(
                video=self.video, param_name=param
            )

        prompts = []
        scenes = parsers.get_scenes()

        voicelines = parsers.get_voiceover_lines()
        for idx, scene in enumerate(scenes, start=1):
            # Check if scene prompts already exist
            prompts_file = os.path.join(
                utils.STORYBOARD_PATH, f"scene_{idx}_prompts.yaml"
            )
            if os.path.exists(prompts_file):
                with open(prompts_file) as single_prompt:
                    logger.info(
                        f"Loading existing prompts from: scene_{idx}_prompts.yaml"
                    )
                    existing_prompt = yaml.load(single_prompt.read().strip(), Loader=yaml.Loader)
                    prompts.append(existing_prompt)
                    continue
            vo_lines_for_scene = [vo_line for vo_line in voicelines if vo_line.scene_index == idx]
            params["input"] = yaml.dump(
            {
                    "scene_description": scene.description,
                    "dialog_lines": [
                        {"line": vo_line.line} for vo_line in vo_lines_for_scene
                    ]
                }
            )
            params["fps"] = 8 # TODO: Make this configurable
            params["duration"] = round(scene.duration)
            params["total_frames"] = params["duration"] * params["fps"]
            scene_prompts = self._call_llm(params )
            # Save prompts file
            with open(prompts_file, "w") as f:
                f.write(yaml.dump(scene_prompts))

            prompts.append(scene_prompts)
   
        # Save the prompts
        with open(os.path.join(utils.PATH_PREFIX, "storyboard_prompts.yaml"), "w") as f:
            f.write(yaml.dump(prompts))

        return prompts

    def check_if_exists(self, idx, output_dir: str) -> tuple[bool, str|None]:
        exists = False
        final_scene_path = os.path.join(output_dir, self.clip_file)
        # If output_dir has a directory in it and inside that directory there is a final.gif, skip
        if os.path.exists(final_scene_path):
            # Check if there is another directory inside
            exists = True
        return exists, final_scene_path

    def generate_scene(self, idx, scene_prompt, scene, output_dir):
        base_prompt_config = "./prompt_travel.json"
        # Read the base prompt config
        with open(base_prompt_config) as f:
            prompt_config = json.load(f)
        # Update the prompt
        prompt_config["path"] = prompt_config["path"] # The model path todo
        prompt_config["head_prompt"] = f"{self.positive_prompt} {scene_prompt['prompt_head']}"
        # get length of scene/vo clip
        prompt_config["prompt_map"] = {
        }
        for kf in scene_prompt["keyframes"]:
            prompt_config["prompt_map"][kf["frame"]] = f"{kf['cameraShot']} {kf['prompt']} and background: {kf['background']}"

        # Apply cameraMovement
        movementStrengthMap = {
            "none": "0.0",
            "low": "0.25",
            "medium": "0.5",
            "high": "1.0",
        }
        if scene_prompt["cameraMovement"] in camera_motion_to_lora_map:
            prompt_config["motion_lora_map"]  = {
                camera_motion_to_lora_map[scene_prompt["cameraMovement"]]: movementStrengthMap[scene_prompt["cameraMovementStrength"].lower()]
            }
        
        prompt_config["n_prompt"] = [
            self.negative_prompt
        ]
        prompt_config["output"]["fps"] = 8

        clip_duration = scene.duration
        clip_duration = round(clip_duration)
        num_frames = clip_duration * prompt_config["output"]["fps"]
        # Save the prompt config
        prompt_config_path = os.path.join(
            self.video.output_dir, f"scene_{idx}_prompt_config.json"
        )
        with open(prompt_config_path, "w") as f:
            json.dump(prompt_config, f)

        # Generate the clip
        # save_dir is the same as output_dir
        save_dir = cli.generate(
            config_path=Path(prompt_config_path),
            width=self.video.production_config.sd_base_image_width,
            height=self.video.production_config.sd_base_image_height,
            length=num_frames,
            save_merged=False,
            use_xformers=True,
            out_dir=output_dir,
            frame_dir="frames",
            out_file="preview.mp4",
        )
        # TODO Move this somewhere more appropriate
        #del cli.g_pipeline
        #del cli.last_model_path
        return save_dir, prompt_config_path
    def make_animated_clip(self):
        clip_directories = []
        scenes = parsers.get_scenes()
        for idx, scene_prompt in enumerate(self.scene_prompts):
            logger.info(f"Generating scene {idx}")
            scene = scenes[idx]
            output_dir = os.path.join(utils.STORYBOARD_PATH, f"scene_{idx}")
            exists, _ = self.check_if_exists(idx, output_dir)
            if exists:
                logger.info(f"Skipping scene {idx} as it already exists")
                clip_directories.append(output_dir)
                continue

            # Check if preview exists
            if os.path.exists(os.path.join(output_dir, "preview.mp4")):
                logger.info(f"Skipping scene {idx} as preview already exists")
                prompt_config_path = os.path.join(
                    self.video.output_dir, f"scene_{idx}_prompt_config.json"
                )
                save_dir = Path(output_dir)
            else:
                torch.cuda.empty_cache()
                save_dir, prompt_config_path = self.generate_scene(idx, scene_prompt, scene, Path(output_dir))
            
            clip_directories.append(output_dir)
            if self.video.production_config.preview:
                logger.info(f"Skipping upscaling scene {idx} as preview is enabled")
                continue
            logger.info(f"Upscaling scene {idx}")
            torch.cuda.empty_cache()
            cli.tile_upscale(
                save_dir.joinpath("frames"),
                config_path=Path(prompt_config_path),
                width=self.video.production_config.video_width,
                out_dir=Path(output_dir),
                no_frames=True,
                upscaled_frames_dir=Path(output_dir).joinpath("frames-upscaled"),
                out_file=Path(output_dir).joinpath("final.mp4"),
            )
        # Concatenate the clips and save the video
        # Write the video list
        video_list = os.path.join(
            utils.STORYBOARD_PATH, "video_list.txt"
        )
        with open(video_list, "w") as f:
            for clip_dir in clip_directories:
                # Find mp4 file
                # Paths are relative to video_list path, so, we remove the prefix
                clip_dir = str(clip_dir).replace(utils.STORYBOARD_PATH, ".", 1)
                f.write(f"file '{clip_dir}/{self.clip_file}'\n")

        command = f"ffmpeg -f concat -safe 0 -i {video_list} -c:v libx264 -preset fast {utils.ANIMATION_VIDEO_FILE}"
        os.system(command)
    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        # initialize agent
        self.initialize_agent()
        self.clip_file = "final.mp4" if not self.video.production_config.preview else "preview.mp4"
        self.make_animated_clip()
        
        return "Done generating animated stuff"

    def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")

    def _call_llm(self, params):
        logger.debug("Calling LLM")
        logger.debug(params)
        retries = 3
        while retries > 0:
            cast_member = self.video.director.get_storyboard_artist()
            chain = llms.get_llm(model=cast_member.model, template=cast_member.prompt)
            try:
                # Use only the title and description lines to save tokens
                response = chain.run(
                    **params,
                )
                logger.debug(response)
                parsed = yaml.load(response, Loader=yaml.Loader)
                ## Check if parsed has the same number of prompts as expected
                ## Check if it has prompt_head (string) and keyframes (array)

                if parsed["prompt_head"] is None or parsed["keyframes"] is None or parsed["cameraMovement"] is None:
                    raise Exception("Invalid prompt")
                
                # Check if keyframes is an array, and its elements have "frame" (int) and "prompt" (string)
                if not isinstance(parsed["keyframes"], list):
                    raise Exception("Invalid keyframes")
                for keyframe in parsed["keyframes"]:
                    if "frame" not in keyframe or "prompt" not in keyframe:
                        raise Exception("Invalid keyframes missing frame or prompt")
                    if not isinstance(keyframe["frame"], int):
                        raise Exception("Invalid keyframes missing frame")
                    if not isinstance(keyframe["prompt"], str):
                        raise Exception("Invalid keyframes missing prompt")
                    if not isinstance(keyframe["background"], str):
                        raise Exception("Invalid keyframes missing background")
                    if not isinstance(keyframe["cameraShot"], str):
                        raise Exception("Invalid keyframes missing cameraShot")
                    
                # Check if prompt_head is a string
                if not isinstance(parsed["prompt_head"], str):
                    raise Exception("Invalid prompt_head")
                
                # Check if the frame numbers are in ascending order starting from 0 and the last
                # frame is less than duration * fps
                if parsed["keyframes"][0]["frame"] != 0:
                    raise Exception("Invalid keyframes")
                for i in range(len(parsed["keyframes"]) - 1):
                    if parsed["keyframes"][i]["frame"] >= parsed["keyframes"][i + 1]["frame"]:
                        raise Exception("Invalid keyframes")
                if parsed["keyframes"][-1]["frame"] > params["duration"] * params["fps"]:
                    raise Exception("Invalid keyframes")
                
                if parsed["cameraMovement"] not in ["PanLeft", "PanRight", "TiltUp", "TiltDown", "RollingClockwise", "RollingAnticlockwise", "ZoomIn", "ZoomOut", None, "None"]:
                    raise Exception("Invalid cameraMovement")

                return parsed
            except Exception as e:
                logger.warning(e)
                logger.info(f"Retrying {retries} more times...")
                retries -= 1

        logger.error("Failed to generate prompts, no more retries left")
        raise Exception("Failed to generate prompts")
