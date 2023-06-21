#!/usr/bin/env python

import pathlib
import torch
import os
import json
from diffusers import DPMSolverMultistepScheduler, StableDiffusionPipeline, StableDiffusionUpscalePipeline
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool
from PIL import Image
from python_on_whales import docker
from typing import Optional, Type
from utils import utils
from xformers.ops import MemoryEfficientAttentionFlashAttentionOp

PREFIX = pathlib.Path(__file__).parent.parent.resolve()


class StoryBoardArtistTool(BaseTool):
    name = "storyboardartist"
    description = "Useful when you need to generate images for the script"

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        # load prompts
        positive_prompt = open("prompts/storyboardartist_positive.txt", "r").read()
        negative_prompt = open("prompts/storyboardartist_negative.txt", "r").read()

        os.makedirs(utils.STORYBOARD_PATH, exist_ok=True)

        # setup stable diffusion pipeline
        pipe = StableDiffusionPipeline.from_pretrained(
                    utils.get_config()["storyboard_artist"]["model"],
                    torch_dtype=torch.float16,
                )
        pipe = pipe.to("cuda")
        pipe.enable_xformers_memory_efficient_attention()
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)

        # settings
        guidance_scale = 7.5
        num_inference_steps = 50
        num_images_per_prompt = 5
        image_height = 432
        image_width = 768

        # enumerate scenes and generate image set
        scenes = utils.get_scenes()
        for i, scene in enumerate(scenes):
            images = pipe(
                    prompt=f"{scene.description}, {positive_prompt}",
                    negative_prompt=negative_prompt,
                    width=image_width,
                    height=image_height,
                    num_inference_steps=num_inference_steps,
                    num_images_per_prompt=num_images_per_prompt,
                    guidance_scale=guidance_scale,
                    ).images
            # enumerate image set and save each image
            for j, image in enumerate(images):
                image.save(os.path.join(utils.STORYBOARD_PATH, f"scene_{i+1}_{j+1}.png"))

        # release models from vram
        del pipe, images, image
        torch.cuda.empty_cache()

        return "Done generating images"

    def _arun(self, query:str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")
