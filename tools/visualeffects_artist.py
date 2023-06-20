#!/usr/bin/env python

import os
import torch

from diffusers import DPMSolverMultistepScheduler, StableDiffusionPipeline, StableDiffusionUpscalePipeline
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool
from PIL import Image
from python_on_whales import docker
from typing import Optional, Type
from utils import utils
from xformers.ops import MemoryEfficientAttentionFlashAttentionOp


class VisualEffectsArtistTool(BaseTool):
    name = "visualeffectsartist"
    description = "Useful for generating visual effects and animations from still images"

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        # enumerate scenes and generate image set
        os.makedirs("ken-burns-effect", exist_ok=True)
        scenes = utils.get_scenes()
        images_per_scene = 5
        for i, scene in enumerate(scenes):
            for j in range(0, images_per_scene):
                # generate "autozoom boomerangs"
                docker.run(
                        "ken-burns-effect",
                        command=[f"python3 autozoom.py --in /mnt/scene_{i+1}_{j+1}.png \
                                --out /mnt/ken-burns-effect/scene_{i+1}_{j+1}.mp4"],
                        volumes=[(os.getcwd(), "/mnt")],
                        remove=True,
                        detach=False,
                        )
                # cut boomerangs into in/out clips
                os.system("""
                        ffmpeg -y -t 2.98 -i ken-burns-effect/scene_{i+1}_{j+1}.mp4 \
                            ken-burns-effect/scene_{i+1}_{j+1}_in.mp4
                """)
                os.system("""
                        ffmpeg -y -sseof -2.98 -i ken-burns-effect/scene_{i+1}_{j+1}.mp4 \
                            ken-burns-effect/scene_{i+1}_{j+1}_out.mp4
                """)
        return "Done generating animations"

    def _arun(self, query:str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")
