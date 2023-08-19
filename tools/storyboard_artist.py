#!usr/bin/env python

import os
import torch
import yaml
import logging

from diffusers import (
    DDIMScheduler,
    StableDiffusionImg2ImgPipeline,
)
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from PIL import Image
from typing import Optional
from utils import llms, utils, parsers, image_gen
from .base import AICPBaseTool

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)


class StoryBoardArtistTool(AICPBaseTool):
    name = "storyboardartist"
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

    def img2img_upscaler(self):
        # setup stable diffusion pipeline
        os.makedirs(os.path.join(utils.STORYBOARD_PATH, "img2img"), exist_ok=True)

        cast_member = self.video.director.get_storyboard_artist()
        pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
            cast_member.sd_model,
            custom_pipeline="lpw_stable_diffusion",
            torch_dtype=torch.float16,
        )

        pipe = pipe.to("cuda")

        pipe.enable_xformers_memory_efficient_attention()
        pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)

        # settings
        guidance_scale = 7.5
        noise_strength = 0.35
        num_inference_steps = 30
        num_images_per_prompt = 1
        num_images_per_scene = self.video.production_config.num_images_per_scene
        image_height = self.video.production_config.video_height
        image_width = self.video.production_config.video_width

        # enumerate scenes and generate image set
        for i, scene in enumerate(self.scene_prompts):
            prompt = f"{scene['prompt']}, {self.positive_prompt}"
            logger.info(f"PP={prompt}")
            logger.info(f"NP={self.negative_prompt}")

            for j in range(0, num_images_per_scene):
                # dont recreate images, its expensive
                if os.path.exists(
                    os.path.join(
                        utils.STORYBOARD_PATH, "img2img", f"scene_{i+1:02}_{j+1:02}.png"
                    )
                ):
                    logger.info(f"Skipping: img2img/scene_{i+1:02}_{j+1:02}.png")
                    continue

                file = os.path.join(
                    utils.STORYBOARD_PATH, f"scene_{i+1:02}_{j+1:02}.png"
                )
                scene_image = Image.open(file).convert("RGB")
                scene_image = scene_image.resize((image_width, image_height))

                image = pipe(
                    prompt=prompt,
                    negative_prompt=self.negative_prompt,
                    image=scene_image,
                    height=image_height,
                    width=image_width,
                    num_inference_steps=num_inference_steps,
                    num_images_per_prompt=num_images_per_prompt,
                    guidance_scale=guidance_scale,
                    strength=noise_strength,
                ).images[0]

                image.save(
                    os.path.join(
                        utils.STORYBOARD_PATH, "img2img", f"scene_{i+1:02}_{j+1:02}.png"
                    )
                )

        # release models from vram
        pipe, scene_image, image = None, None, None
        del pipe, scene_image, image
        torch.cuda.empty_cache()

        return "Done generating images"

    def stable_diffusion(self):
        # setup stable diffusion pipeline
        cast_member = self.video.director.get_storyboard_artist()
        lora_paths = []
        for actor in self.video.actors:
            if not actor.lora_keyword:
                continue
            lora_paths.append(
                os.path.join("loras", f"{actor.lora_keyword}.safetensors")
            )

        pipe = image_gen.get_pipeline_with_loras(cast_member.sd_model, lora_paths)
        # settings
        guidance_scale = 7.5
        num_inference_steps = 50
        num_images_per_prompt = self.video.production_config.num_images_per_scene
        image_width = self.video.production_config.sd_base_image_width
        image_height = self.video.production_config.sd_base_image_height

        # enumerate scenes and generate image set
        for i, scene in enumerate(self.scene_prompts):
            # dont recreate images, its expensive
            if os.path.exists(
                os.path.join(
                    utils.STORYBOARD_PATH, f"scene_{i+1:02}_{num_images_per_prompt}.png"
                )
            ):
                logger.info(f"Skipping: scene_{i+1:02}_{num_images_per_prompt}.png")
                continue

            prompt = f"{scene['prompt']}, {self.positive_prompt}"

            logger.info(f"PP={prompt}")
            logger.info(f"NP={self.negative_prompt}")

            images = pipe(
                prompt=prompt,
                negative_prompt=self.negative_prompt,
                width=image_width,
                height=image_height,
                num_inference_steps=num_inference_steps,
                num_images_per_prompt=num_images_per_prompt,
                guidance_scale=guidance_scale,
            ).images

            # enumerate image set and save each image
            for j, image in enumerate(images):
                image.save(
                    os.path.join(utils.STORYBOARD_PATH, f"scene_{i+1:02}_{j+1:02}.png")
                )

        # release models from vram
        pipe, images, image = None, None, None
        del pipe, images, image
        torch.cuda.empty_cache()

        return "Done generating images"

    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        # initialize agent
        self.initialize_agent()

        # generate images
        self.stable_diffusion()

        # upscale images with img2img
        self.img2img_upscaler()

        return "Done generating storyboard"

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
