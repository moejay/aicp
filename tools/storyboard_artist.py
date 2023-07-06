#!usr/bin/env python

import os
import torch
import yaml

from diffusers import DPMSolverMultistepScheduler, StableDiffusionPipeline, StableDiffusionImg2ImgPipeline
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from PIL import Image
from python_on_whales import docker
from typing import Optional
from utils import llms, utils, parsers

from .base import AICPBaseTool

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
        cast_member = self.director.get_storyboard_artist()
        self.positive_prompt = cast_member.positive_prompt
        self.negative_prompt = cast_member.negative_prompt
    
        # load storyboard artist prompts if they exist or create them 
        prompts_file = os.path.join(utils.PATH_PREFIX, "storyboard_prompts.yaml")
        if os.path.exists(prompts_file):
            with open(prompts_file) as prompts:
                print("Loading existing prompts from: storyboard_prompts.yaml")
                self.scene_prompts = yaml.load(prompts.read().strip(), Loader=yaml.Loader)
        else:
            print("Generating text-to-image prompts for storyboard artist...")
            self.scene_prompts = self.ego()

    def ego(self):
        """ Run the script through the mind of the storyboard artist
            to generate more descriptive prompts """
        cast_member = self.director.get_storyboard_artist()
        chain = llms.get_llm(model=cast_member.model, template=cast_member.prompt)
        # Use only the description lines to save tokens
        script_input = yaml.dump([
                {"description": s["description"]} \
                   for s in parsers.get_script()
            ])
        response = chain.run(script_input)
        print(response)

        # Save the updated script
        with open(os.path.join(utils.PATH_PREFIX, "storyboard_prompts.yaml"), "w") as f:
            f.write(response)

        return yaml.load(response, Loader=yaml.Loader)

    def gfp_upscaler(self):
        """ Upscale images with the GFPGAN ("restore faces") """
        out = docker.run(
            "gfpgan:latest",
            [
                "python3", "/app/GFPGAN/inference_gfpgan.py",
                "-i", f"/mnt/{utils.PATH_PREFIX}/storyboard",
                "-o", f"/mnt/{utils.PATH_PREFIX}/storyboard",
                "-v", "1.3",
                "-s", "2",
                "--ext", "png"
            ],
            user=os.getuid(),
            volumes=[(os.getcwd(), "/mnt")],
            gpus=1,
            remove=True,
            detach=False,
            tty=True,
        )
        print(out)
        return True

    def img2img_upscaler(self):
        # setup stable diffusion pipeline
        os.makedirs(os.path.join(utils.STORYBOARD_PATH, "img2img"), exist_ok=True)

        cast_member = self.director.get_storyboard_artist()
        pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
                    cast_member.sd_model,
                    custom_pipeline="lpw_stable_diffusion",
                    torch_dtype=torch.float16,
                )
        pipe = pipe.to("cuda")

        pipe.enable_xformers_memory_efficient_attention()
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
        #scheduler.config.algorithm_type = "sde-dpmsolver++"
        #pipe.scheduler = scheduler

        # settings
        guidance_scale = 7.5
        noise_strength = 0.75
        num_inference_steps = 30 
        num_images_per_prompt = 1
        num_images_per_scene = 10
        image_height = self.production_config.video_height
        image_width = self.production_config.video_width 

        # enumerate scenes and generate image set
        for i, scene in enumerate(self.scene_prompts):
            prompt = f"{scene['prompt']}, {self.positive_prompt}"
            print(f"PP={prompt}")
            print(f"NP={self.negative_prompt}")

            for j in range(0, num_images_per_scene):
                # dont recreate images, its expensive
                if os.path.exists(os.path.join(utils.STORYBOARD_PATH, "img2img", f"scene_{i+1}_{j+1}.png")):
                    print(f"Skipping: img2img/scene_{i+1}_{j+1}.png")
                    continue

                file = os.path.join(utils.STORYBOARD_PATH, f"scene_{i+1}_{j+1}.png")
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

                image.save(os.path.join(utils.STORYBOARD_PATH, "img2img", f"scene_{i+1}_{j+1}.png"))

        # release models from vram
        pipe, scene_image, image = None, None, None
        del pipe, scene_image, image
        torch.cuda.empty_cache()

        return "Done generating images"

    def stable_diffusion(self):
        # setup stable diffusion pipeline
        cast_member = self.director.get_storyboard_artist()
        pipe = StableDiffusionPipeline.from_pretrained(
                    cast_member.sd_model,
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
        num_images_per_prompt = 10
        image_width = self.production_config.sd_base_image_width 
        image_height = self.production_config.sd_base_image_height

        # enumerate scenes and generate image set
        for i, scene in enumerate(self.scene_prompts):
            # dont recreate images, its expensive
            if os.path.exists(os.path.join(utils.STORYBOARD_PATH, f"scene_{i+1}_{num_images_per_prompt}.png")):
                print(f"Skipping: scene_{i+1}_{num_images_per_prompt}.png")
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
                image.save(os.path.join(utils.STORYBOARD_PATH, f"scene_{i+1}_{j+1}.png"))

        # release models from vram
        pipe, images, image = None, None, None
        del pipe, images, image
        torch.cuda.empty_cache()

        return "Done generating images"

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        # initialize agent
        self.initialize_agent()

        # generate images
        self.stable_diffusion()

        # upscale images with img2img
        self.img2img_upscaler()

        # upscale with restore faces
        #self.gfp_upscaler()

        return "Done generating storyboard"

    def _arun(self, query:str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")
