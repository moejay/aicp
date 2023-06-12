#!/usr/bin/env python

from typing import Optional, Type

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool
import torch
from diffusers import StableDiffusionPipeline

class StoryBoardArtistTool(BaseTool):
    name = "storyboardartist"
    description = "Useful when you need to generate images for the script"

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        pipe = StableDiffusionPipeline.from_pretrained("dreamlike-art/dreamlike-photoreal-2.0", torch_dtype=torch.float16)
        pipe = pipe.to("cuda")
        lines = open("script.txt", "r").readlines()
        scene_lines = [line.strip() for line in lines if line.startswith("[Scene")]
        for i, line in enumerate(scene_lines):
            pipe(line).images[0].save(f"scene_{i + 1}.png")
        return "Done generating images"

    def _arun(self, query:str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")
