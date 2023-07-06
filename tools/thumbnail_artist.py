import os
import torch
import yaml

from typing import Optional
from diffusers import DPMSolverMultistepScheduler, StableDiffusionPipeline
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from typing import Optional
from utils import utils, llms, parsers
from .base import AICPBaseTool


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
        cast_member = self.director.get_thumbnail_artist()
        self.positive_prompt = cast_member.positive_prompt
        self.negative_prompt = cast_member.negative_prompt
    
        # load storyboard artist prompts if they exist or create them 
        prompts_file = os.path.join(utils.PATH_PREFIX, "thumbnail_prompts.yaml")
        if os.path.exists(prompts_file):
            with open(prompts_file) as prompts:
                print(f"Loading existing prompts from: {prompts_file}")
                self.scene_prompts = yaml.load(prompts.read().strip(), Loader=yaml.Loader)
        else:
            print("Generating text-to-image prompts for thumbnail artist...")
            self.scene_prompts = self.ego()

    def ego(self):
        """ Run the script through the mind of the storyboard artist
            to generate more descriptive prompts """
        cast_member = self.director.get_thumbnail_artist()
        chain = llms.get_llm(model=cast_member.model, template=cast_member.prompt)
        # Use only the description lines to save tokens
        script_input = yaml.dump([
                {"description": s["description"]} \
                   for s in parsers.get_script()
            ])

        response = chain.run(script_input)
        print(response)

        # Save the updated script
        with open(os.path.join(utils.PATH_PREFIX, "thumbnail_prompts.yaml"), "w") as f:
            f.write(response)

        return yaml.load(response, Loader=yaml.Loader)
    def stable_diffusion(self):
        # setup stable diffusion pipeline
        cast_member = self.director.get_thumbnail_artist()
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
        num_images_per_prompt = 2
        image_height = self.production_config.sd_base_image_height
        image_width = self.production_config.sd_base_image_width 

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

    
