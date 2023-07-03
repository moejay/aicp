from typing import Optional
import os
import yaml
from diffusers import DPMSolverMultistepScheduler, StableDiffusionPipeline, StableDiffusionImg2ImgPipeline, StableDiffusionUpscalePipeline
from xformers.ops import MemoryEfficientAttentionFlashAttentionOp
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain import LLMChain
from langchain.prompts.chat import (ChatPromptTemplate, SystemMessagePromptTemplate, AIMessagePromptTemplate, HumanMessagePromptTemplate)
import json

from utils import utils, llms
from .base import AICPBaseTool

import torch
from diffusers import StableDiffusionPipeline


class ThumbnailArtistTool(AICPBaseTool):
    """Useful when you need to create a thumbnail for your video"""
    name = "thumbnailartist"
    description = "Useful when you need to create a thumbnail for your video"

    scene_prompts = []
    positive_prompt = ""
    negative_prompt = ""
    def initialize_agent(self):
        super().initialize_agent()
        self.load_prompts()

    def load_prompts(self):
        # load additive prompts
        self.positive_prompt = open("prompts/storyboard_artist/positive.txt", "r").read().strip()
        self.negative_prompt = open("prompts/storyboard_artist/negative.txt", "r").read().strip()
    
        # load storyboard artist prompts if they exist or create them 
        prompts_file = os.path.join(utils.PATH_PREFIX, "thumbnail_prompts.json")
        if os.path.exists(prompts_file):
            with open(prompts_file) as prompts:
                print(f"Loading existing prompts from: {prompts_file}")
                self.scene_prompts = json.loads(prompts.read().strip())
        else:
            print("Generating text-to-image prompts for thumbnail artist...")
            self.scene_prompts = self.ego()

    def ego(self):
        """ Run the script through the mind of the storyboard artist
            to generate more descriptive prompts """
        template = open("prompts/thumbnail_artist.txt").read()
        chain = llms.get_llm(model=utils.get_config()["thumbnail_artist"]["ego_model"], template=template)
        # Use only the description lines to save tokens
        script_input = yaml.dump([
                {"description": s["description"]} \
                   for s in utils.get_script()
            ])

        response = chain.run(script_input)
        print(response)

        # Save the updated script
        with open(os.path.join(utils.PATH_PREFIX, "thumbnail_prompts.json"), "w") as f:
            f.write(response)

        return json.loads(response)
    def stable_diffusion(self):
        # setup stable diffusion pipeline
        pipe = StableDiffusionPipeline.from_pretrained(
                    utils.get_config()["thumbnail_artist"]["sd_model"],
                    custom_pipeline="lpw_stable_diffusion",
                    torch_dtype=torch.float16,
                )
        pipe = pipe.to("cuda")
        pipe.enable_xformers_memory_efficient_attention()
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
#        scheduler.config.algorithm_type = "sde-dpmsolver++"
#        pipe.scheduler = scheduler


        # settings
        guidance_scale = 7.5
        num_inference_steps = 50 
        num_images_per_prompt = 2
        image_height = 432
        image_width = 768

        # enumerate scenes and generate image set
        for i, scene in enumerate(self.scene_prompts):
            # dont recreate images, its expensive
            if os.path.exists(os.path.join(utils.THUMBNAILS_PATH, f"thumbnail_{i+1}_{num_images_per_prompt}.jpg")):
                print(f"Skipping: thumbnail_{i+1}_{num_images_per_prompt}.jpg")
                continue

            prompt = f"{scene['prompt']}, {self.positive_prompt}"

            print(f"PP={prompt}")
            print(f"NP={self.negative_prompt}")

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
                image.save(os.path.join(utils.THUMBNAILS_PATH, f"thumbnail_{i+1}_{j+1}.jpg"))

        # release models from vram
        pipe, images, image = None, None, None
        del pipe, images, image
        torch.cuda.empty_cache()

        return "Done generating images"


    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""

        # Come up with an enticing text for the thumbnail
        # Come up with an enticing image for the thumbnail
        self.initialize_agent()

        self.stable_diffusion()

        # TODO Generate the text 
        # TODO Combine the text and the image

        return "Done generating thumbnails"


    def _arun(self, query:str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")

    
