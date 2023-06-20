#!/usr/bin/env python

import torch
import os
from diffusers import DPMSolverMultistepScheduler, StableDiffusionPipeline, StableDiffusionUpscalePipeline
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool
from PIL import Image
from python_on_whales import docker
from typing import Optional, Type
from utils import utils
from xformers.ops import MemoryEfficientAttentionFlashAttentionOp


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
                image.save(f"scene_{i+1}_{j+1}.png")

        # release models from vram
        del pipe, images, image
        torch.cuda.empty_cache()

        # upscaler pipeline
        #upscaler_diffuser()
        upscale_gfpgan()

        return "Done generating images"

    def _arun(self, query:str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")

def upscale_diffuser():
    # setup stable diffusion upscaler
    pipe = StableDiffusionUpscalePipeline.from_pretrained(
            "stabilityai/stable-diffusion-x4-upscaler",
            revision="fp16",
            torch_dtype=torch.float16,
            )
    pipe = pipe.to("cuda")
    pipe.enable_xformers_memory_efficient_attention(attention_op=MemoryEfficientAttentionFlashAttentionOp)
    pipe.vae.enable_xformers_memory_efficient_attention(attention_op=None)
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)

    # upscaler settings
    guidance_scale = 6.5
    num_inference_steps = 20
    num_images_per_prompt = 1

    # enumerate over images and upscale
    for i, scene in enumerate(scenes):
        for j in range(0,5):
            low_res_image = Image.open(f"scene_{i+1}_{j+1}.png").convert("RGB")
            #low_res_image = low_res_image.resize((384,216))

            image = pipe(
                    image=low_res_image,
                    prompt=f"{scene.description}, {positive_prompt}",
                    negative_prompt=negative_prompt,
                    num_inference_step=up_num_inference_steps,
                    num_images_per_prompt=up_num_images_per_prompt,
                    ).images[0]
            image.save(f"scene_upscaled_{i+1}_{j+1}.png")

    # release models from vram
    del pipe, image
    torch.cuda.empty_cache()

def upscale_gfpgan():
    # use gfpgan "restore faces" upscaler 
    docker.run(
            "gfpgan:latest",
            ["/bin/bash", "-c", "for i in /mnt/*.png; do python3 GFPGAN/inference_gfpgan.py -i $i -o /mnt -v 1.3 -s 2; done"],
            volumes=[(os.getcwd(), "/mnt")],
            remove=True,
            detach=False,
            )
