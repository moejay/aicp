#!/usr/bin/env python

import glob
import json
import os
import torch
import yaml

from diffusers import DPMSolverMultistepScheduler, StableDiffusionPipeline, StableDiffusionUpscalePipeline
from langchain import LLMChain
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.prompts.chat import (ChatPromptTemplate, SystemMessagePromptTemplate, AIMessagePromptTemplate, HumanMessagePromptTemplate)
from langchain.tools import BaseTool
from PIL import Image
from python_on_whales import docker
from typing import Optional, Type
from utils import llms, utils
from xformers.ops import MemoryEfficientAttentionFlashAttentionOp


class StoryBoardArtistTool(BaseTool):
    name = "storyboardartist"
    description = "Useful when you need to generate images for the script"

    scene_prompts = []
    positive_prompt = ""
    negative_prompt = ""


    def ego(self):
        """ Run the script through the mind of the storyboard artist
            to generate more descriptive prompts """
        llm = llms.RevGPTLLM(model=utils.get_config()["storyboard_artist"]["ego_model"])
        template = open("prompts/storyboard_artist.txt").read()

        system_message_prompt = SystemMessagePromptTemplate.from_template(template)
        human_message_prompt = HumanMessagePromptTemplate.from_template("{script}")

        chat_prompt = ChatPromptTemplate.from_messages([
                system_message_prompt,
                human_message_prompt
            ])

        # Use only the description lines to save tokens
        script_input = yaml.dump([
                {"description": s["description"]} \
                   for s in utils.get_script()
            ])

        chain = LLMChain(llm=llm, prompt=chat_prompt)
        response = chain.run(script=script_input)
        print(response)

        # Save the updated script
        with open(os.path.join(utils.PATH_PREFIX, "prompts.json"), "w") as f:
            f.write(response)

        return json.loads(response)

    def gfp_upscaler(self):
        """ Upscale images with the GFPGAN ("restore faces") """
        out = docker.run(
            "gfpgan:latest",
            [
                "python3", "/app/GFPGAN/inference_gfpgan.py",
                "-i", "/mnt/output/storyboard",
                "-o", "/mnt/output/storyboard",
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

    def upscaler(self, scenes):
        """ Upscale images using the upscale diffuser (memory exhaustion issues) """
        #os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:512"
        out_path = os.path.join(utils.STORYBOARD_PATH, "upscaled")
        os.makedirs(out_path, exist_ok=True)

        model_id = "stabilityai/stable-diffusion-x4-upscaler"
        pipe = StableDiffusionUpscalePipeline.from_pretrained(
                model_id,
                revision="fp16",
                torch_dtype=torch.float16
            ).to("cuda")
        pipe.enable_xformers_memory_efficient_attention(attention_op=MemoryEfficientAttentionFlashAttentionOp)
        pipe.vae.enable_xformers_memory_efficient_attention(attention_op=None)
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)

        # settings
        guidance_scale = 7.5
        num_inference_steps = 20
        num_images_per_prompt = 1

        # images/scenes
        for i, scene in enumerate(scenes):
            prompt = f"{scene.storyboard_prompt} {self.positive_prompt}"
            for image in glob.glob(os.path.join(utils.STORYBOARD_PATH, f"scene_{i}_*.png")):
                file_name = os.path.basename(image)
                low_res_img = Image.open(image).convert("RGB")

                upscaled_image = pipe(
                        prompt=prompt,
                        image=low_res_img,
                        num_inference_steps=num_inference_steps,
                        num_images_per_prompt=num_images_per_prompt,
                        guidance_scale=guidance_scale,
                    ).image[0]
                upscaled_image.save(os.path.join(out_path, file_name))

        # release models from vram
        del pipe, upscaled_image
        torch.cuda.empty_cache()

        return True

    def load_prompts(self):
        self.positive_prompt = open("prompts/storyboardartist_positive.txt", "r").read().strip()
        self.negative_prompt = open("prompts/storyboardartist_negative.txt", "r").read().strip()

    def stable_diffusion(self):
        # setup stable diffusion pipeline
        pipe = StableDiffusionPipeline.from_pretrained(
                    utils.get_config()["storyboard_artist"]["sd_model"],
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
        image_height = 432
        image_width = 768

        # enumerate scenes and generate image set
        for i, scene in enumerate(self.scene_prompts):
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
        del pipe, images, image
        torch.cuda.empty_cache()

        return "Done generating images"

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        # improvise prompts from script descriptions
        self.scene_prompts = self.ego()

        # load prompt add-ons
        self.load_prompts()

        # generate images
        self.stable_diffusion()

        # upscale images
        #self.upscaler(scenes)

        # upscale with restore faces
        self.gfp_upscaler()

        return "Done generating storyboard"

    def _arun(self, query:str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")
