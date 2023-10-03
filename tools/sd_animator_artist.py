#!usr/bin/env python

import json
import os
from pathlib import Path
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


class SDAnimatorArtist(AICPBaseTool):
    name = "sdanimatorartist"
    description = "Useful when you need to generate images for the script"

    scene_prompts = []
    positive_prompt = ""
    negative_prompt = ""

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
        if self.video.production_config.voiceline_synced_storyboard:
            with open(utils.SCRIPT_SUMMARY, "r") as f:
                script_summary = f.read()

            # Do it per scene and provide the dialog lines
            vo_lines = parsers.get_voiceover_lines()
            # Group by scene
            for scene_index, scene in enumerate(parsers.get_scenes()):
                logger.info(f"Generating prompts for scene {scene_index}")
                # If we already have prompts for this scene, load them
                prompts_file = os.path.join(
                    utils.STORYBOARD_PATH, f"scene_{scene_index}_prompts.yaml"
                )
                if os.path.exists(prompts_file):
                    with open(prompts_file) as prompts:
                        logger.info(
                            f"Loading existing prompts from: scene_{scene_index}_prompts.yaml"
                        )
                        prompts = yaml.load(prompts.read().strip(), Loader=yaml.Loader)
                        prompts.extend(prompts)
                        continue

                vo_lines_for_scene = [
                    vo_line
                    for vo_line in vo_lines
                    if vo_line.scene_index == scene_index
                ]

                if len(vo_lines_for_scene) > 10:
                    logger.info(
                        f"Splitting scene {scene_index} into multiple prompts because it has {len(vo_lines_for_scene)} lines"
                    )
                    # Group and split by line_index as well
                    # Get all the line indexes
                    line_indexes = set(
                        [vo_line.line_index for vo_line in vo_lines_for_scene]
                    )
                    # Group by line index
                    vo_lines_for_scene = [
                        [
                            vo_line
                            for vo_line in vo_lines_for_scene
                            if vo_line.line_index == line_index
                        ]
                        for line_index in sorted(line_indexes)
                    ]
                    # call llm for each group
                    scene_prompts = []
                    for vo_lines_for_line_index in vo_lines_for_scene:
                        logger.info(
                            f"Generating prompts for scene {scene_index} line {vo_lines_for_line_index[0].line_index}"
                        )
                        params["input"] = yaml.dump(
                            {
                                "script_summary": script_summary,
                                "scene_title": scene.scene_title,
                                "scene_description": scene.description,
                                "number_of_expected_prompts": len(
                                    vo_lines_for_line_index
                                ),
                                "dialog_lines": [
                                    {"actor": vo_line.actor.name, "line": vo_line.line}
                                    for vo_line in vo_lines_for_line_index
                                ],
                            }
                        )
                        scene_prompts.extend(
                            self._call_llm(params, len(vo_lines_for_line_index))
                        )

                else:
                    logger.info(f"Generating prompts for scene {scene_index}")
                    params["input"] = yaml.dump(
                        {
                            "script_summary": script_summary,
                            "scene_title": scene.scene_title,
                            "scene_description": scene.description,
                            "number_of_expected_prompts": len(vo_lines_for_scene),
                            "dialog_lines": [
                                {"line": vo_line.line} for vo_line in vo_lines_for_scene
                            ],
                        }
                    )
                    scene_prompts = self._call_llm(params, len(vo_lines_for_scene))
                prompts.extend(scene_prompts)
                # Save the prompts so we don't recompute them if failure
                with open(
                    prompts_file,
                    "w",
                ) as f:
                    f.write(yaml.dump(scene_prompts))
        else:
            params["input"] = yaml.dump(
                [
                    {
                        "scene_title": s.scene_title,
                        "scene_description": s.description,
                    }
                    for s in parsers.get_scenes()
                ]
            )
            prompts = self._call_llm(params, len(parsers.get_scenes()))

        # Save the prompts
        with open(os.path.join(utils.PATH_PREFIX, "storyboard_prompts.yaml"), "w") as f:
            f.write(yaml.dump(prompts))

        return prompts

    def make_animated_clip(self):
        vo_lines = parsers.get_voiceover_lines()
        scenes = parsers.get_scenes()
        clip_directories = []
        for idx, scene in enumerate(self.scene_prompts):
            logger.info(f"Generating scene {idx} with prompt: {scene['prompt']}")
            output_dir = os.path.join(utils.STORYBOARD_PATH, f"scene_{idx}")
            # If output_dir has a directory in it and inside that directory there is a final.gif, skip
            if os.path.exists(output_dir):
                # Check if there is another directory inside
                dirs = os.listdir(output_dir)
                if len(dirs) > 0:
                    # Check if there is a final.gif inside
                    final_scene_path = os.path.join(output_dir, dirs[0])
                    if "final.gif" in os.listdir(final_scene_path):
                        logger.info(
                            f"Skipping scene {idx} because it already exists in {final_scene_path}"
                        )
                        clip_directories.append(final_scene_path)
                        continue



            base_prompt_config = "data/prompt_travel.json"
            # Read the base prompt config
            with open(base_prompt_config) as f:
                prompt_config = json.load(f)
            # Update the prompt
            prompt_config["path"] = prompt_config["path"] # The model path todo
            prompt_config["head_prompt"] = self.positive_prompt 
            # get length of scene/vo clip
            prompt_config["prompt_map"] = {
                "0": scene["prompt"] 
            }
            prompt_config["n_prompt"] = [
                self.negative_prompt
            ]
            prompt_config["output"]["fps"] = 8
            clip_duration = 0
            if self.video.production_config.voiceline_synced_storyboard:
                vo_line = vo_lines[idx]
                clip_duration = vo_line.duration
            else:
                clip_duration = scenes[idx].duration
            
            clip_duration = round(clip_duration)
            num_frames = clip_duration * prompt_config["output"]["fps"]
            # Save the prompt config
            prompt_config_path = os.path.join(
                self.video.output_dir, f"scene_{idx}_prompt_config.json"
            )
            with open(prompt_config_path, "w") as f:
                json.dump(prompt_config, f)

            # Generate the clip
            save_dir = cli.generate(
                config_path=Path(prompt_config_path),
                width=self.video.production_config.sd_base_image_width,
                height=self.video.production_config.sd_base_image_height,
                length=num_frames,
                save_merged=True,
                out_dir=Path(output_dir),
            )
            clip_directories.append(save_dir)
        # Concatenate the clips and save the video
        # Write the video list
        video_list = os.path.join(
            utils.STORYBOARD_PATH, "video_list.txt"
        )
        with open(video_list, "w") as f:
            for clip_dir in clip_directories:
                f.write(f"file '{clip_dir}/final.gif'\n")

        command = f"ffmpeg -f concat -safe 0 -i {video_list} -c copy {utils.ANIMATION_VIDEO_FILE}"
        return command
    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        # initialize agent
        self.initialize_agent()

        self.make_animated_clip()

        
        return "Done generating animated stuff"

    def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")

    def _call_llm(self, params, expected_number_of_prompts):
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
                if len(parsed) != expected_number_of_prompts:
                    logger.info(
                        f"Unexpected number of prompts: {len(parsed)} != {expected_number_of_prompts}"
                    )
                    raise Exception("Unexpected number of prompts")
                return parsed
            except Exception as e:
                logger.warning(e)
                logger.info(f"Retrying {retries} more times...")
                retries -= 1

        logger.error("Failed to generate prompts, no more retries left")
        raise Exception("Failed to generate prompts")
