#!/usr/bin/env python

import torch

from diffusers import DPMSolverMultistepScheduler, StableDiffusionPipeline, StableDiffusionUpscalePipeline
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool
from PIL import Image
from typing import Optional, Type
from utils import utils
from xformers.ops import MemoryEfficientFlashAttentionOp


class StoryBoardArtistTool(BaseTool):
    name = "storyboardartist"
    description = "Useful when you need to generate images for the script"

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        # load prompts
        positive_prompt = open("prompts/storyboardartist_positive.txt", "r").read()
        negative_prompt = open("prompts/storyboardartist_negative.txt", "r").read()

        # setup stable diffusion pipeline
        pipe = StableDiffusionPipeline.from_pretrained(
                "SG161222/Realistic_Vision_V2.0",
                torch_dtype=torch.float16,
                )
        pipe = pipe.to("cuda")
        pipe.enable_xformers_memory_efficient_attention()
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)

        # settings
        sd_guidance_scale = 0.7
        sd_num_inference_steps = 50
        sd_num_images_per_prompt = 5

        # enumerate scenes and generate image set
        scenes = utils.get_scenes()
        for i, scene in enumerate(scenes):
            images = pipe(
                    prompt=f"{scene.description}, {positive_prompt}",
                    negative_prompt=negative_prompt,
                    num_inference_steps=sd_num_inference_steps,
                    num_images_per_prompt=sd_num_images_per_prompt,
                    ).images
            # enumerate image set and save each image
            for j, image in enumerate(images):
                image.save(f"scene_{i+1}_{j+1}.png")

        # release models from vram
        del pipe
        torch.cuda.empty_cache()

        # setup stable diffusion upscaler
        pipe = StableDiffusionUpscalePipeline.from_pretrained(
                "stabilityai/stable-diffusion-x4-upscaler",
                revision="fp16",
                torch_dtype=torch.float16,
                )
        pipe = pipe.to("cuda")
        pipe.enable_xformers_memory_efficient_attention(attention_op=MemoryEfficientAttentionFlashAttentionOp)
        pipe.vae.enable_xformers_memory_efficient_attention(attention_op=None)
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipeline.scheduler.config)

        # upscaler settings
        up_guidance_scale = 0.7
        up_num_inference_steps = 20
        up_num_images_per_prompt = 1

        # enumerate over images and upscale
        for i, scene in enumerate(scenes):
            for j in range(sd_num_images_per_prompt):
                low_res_image = Image.open(f"scene_{i+1}_{j+1}.png").convert("RGB")
                image = pipeline(
                        prompt=f"{scene.description}, {positive_prompt}",
                        negative_prompt=negative_prompt,
                        image=low_res_image,
                        num_inference_step=up_num_inference_steps,
                        num_images_per_prompt=up_num_images_per_prompt,
                        ).images[0]
                image.save(f"scene_upscaled_{i+1}_{j+1}.png")

        return "Done generating images"

    def _arun(self, query:str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")
