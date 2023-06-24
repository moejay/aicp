#!/usr/bin/env python

import torch
import os
import json
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

    def ego(self):
        """ Run the script through the mind of the storyboard artist
            to generate more descriptive prompts """
        llm = llms.RevGPTLLM(model="gpt-3.5")
        template = open("prompts/storyboard_artist.txt").read()

        system_message_prompt = SystemMessagePromptTemplate.from_template(template)
        human_message_prompt = HumanMessagePromptTemplate.from_template("{script}")
        chat_prompt = ChatPromptTemplate.from_messages([
                system_message_prompt,
                human_message_prompt
            ])

        chain = LLMChain(llm=llm, prompt=chat_prompt)
        script_input = yaml.dump([
                {"description": s["description"]} \
                   for s in utils.get_script()
            ])
        response = chain.run(script=script_input)

        # Use only the description lines to save tokens
        updated_scenes = []
        for updated, old in zip(json.loads(response), utils.get_scenes()):
            updated_scene = old
            updated_scene.content = updated["description"]
            updated_scenes.append(updated_scene)

        # Save the updated script
        with open(f"{utils.SCRIPT}.storyboard", "w") as f:
            f.write(yaml.dump(updated_scenes))

        return updated_scenes


    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        # load prompts
        scenes = self.ego()

        positive_prompt = open("prompts/storyboardartist_positive.txt", "r").read()
        negative_prompt = open("prompts/storyboardartist_negative.txt", "r").read()
        negative_prompt_count = len(negative_prompt.split(" "))

        # setup stable diffusion pipeline
        pipe = StableDiffusionPipeline.from_pretrained(
                    utils.get_config()["storyboard_artist"]["model"],
                    torch_dtype=torch.float16,
                )
        pipe = pipe.to("cuda")
        pipe.enable_xformers_memory_efficient_attention()
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)

        # tokenizers
        max_length = pipe.tokenizer.model_max_length

        # settings
        guidance_scale = 7.5
        num_inference_steps = 50
        num_images_per_prompt = 10
        image_height = 432
        image_width = 768

        # enumerate scenes and generate image set
        #scenes = utils.get_scenes()
        for i, scene in enumerate(scenes):
            prompt = f"{scene.content}, {positive_prompt}"
            prompt_count = len(prompt.split(" "))

            # create tensor based on whichever is longer
            if prompt_count >= negative_prompt_count:
                input_ids = pipe.tokenizer(
                        prompt,
                        return_tensors="pt",
                        truncation=False
                    ).input_ids.to("cuda")
                shape_max_length = input_ids.shape[-1]
                negative_ids = pipe.tokenizer(
                        negative_prompt,
                        truncation=False,
                        padding="max_length",
                        max_length=shape_max_length,
                        return_tensors="pt"
                    ).input_ids.to("cuda")
            else:
                negative_ids = pipe.tokenizer(
                        negative_prompt,
                        return_tensors="pt",
                        truncation=False
                    ).input_ids.to("cuda")
                shape_max_length = negative_ids.shape[-1]
                input_ids = pipe.tokenizer(
                        prompt,
                        return_tensors="pt",
                        truncation=False,
                        padding="max_length",
                        max_length=shape_max_length
                    ).input_ids.to("cuda")

            # embeds
            concat_embeds = []
            neg_embeds = []
            for j in range(0, shape_max_length, max_length):
                concat_embeds.append(pipe.text_encoder(input_ids[:, j: j + max_length])[0])
                neg_embeds.append(pipe.text_encoder(negative_ids[:, j: j + max_length])[0])

            prompt_embeds = torch.cat(concat_embeds, dim=1)
            negative_prompt_embeds = torch.cat(neg_embeds, dim=1)

            images = pipe(
                    prompt_embeds=prompt_embeds,
                    negative_prompt_embeds=negative_prompt_embeds,
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
