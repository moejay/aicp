"""This is where we make videoclip layers for the clop."""
from __future__ import annotations
import json
import os
import uuid
from langchain.callbacks.file import FileCallbackHandler
from langchain.callbacks.stdout import StdOutCallbackHandler
from langchain.prompts.base import StringPromptValue
from backend import settings

from backend.models import (
    AICPClip,
    AICPProject,
    AICPScript,
    AICPOutline,
    AICPSequence,
    AICPScene,
    AICPShot,
    AICPActor,
    AICPVideoLayer,
    AICPStoryboardArtist
)
from backend.utils import llms
from utils import parsers
from typing import Any

from pydantic import Extra

from langchain.schema.language_model import BaseLanguageModel
from langchain.callbacks.manager import (
    AsyncCallbackManagerForChainRun,
    CallbackManagerForChainRun,
)
from langchain.chains.base import Chain


class LayerVideoclipChain(Chain):
    """
    Generates a video outline based on a script.
    """

    llm: BaseLanguageModel
    output_key: str = "text"  #: :meta private:

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid
        arbitrary_types_allowed = True

    @property
    def input_keys(self) -> list[str]:
        """Will be whatever keys the prompt expects.

        :meta private:
        """
        return ["text"]

    @property
    def output_keys(self) -> list[str]:
        """Will always return text key.

        :meta private:
        """
        return [self.output_key]

    def _call(
        self,
        inputs: dict[str, Any],
        run_manager: CallbackManagerForChainRun | None = None,
    ) -> dict[str, str]:
        """Runs the chain."""
        
        text = inputs["text"]
        
        input_value = f"""
        How to define a video clip:
        {{
            "prompt": "A description of what you percieve as the first frame of the video clip",
            "camera": "A description of the camera movement",
            "action": "A description of the actions in the video clip, someone talking, walking, etc. an object moving, glowing etc.",
        }}
        Given the following information about a shot:
        {text}
        Create a video clip definition based on the shot.

        Remember the video clip definitions above.
        """
        result = self.llm.generate_prompt(
            [StringPromptValue(text=input_value)],
            callbacks=run_manager.get_child() if run_manager else None,
        )
        if run_manager:
            run_manager.on_text(result.generations[0][0].text)

        return {self.output_key: result.generations[0][0].text}

    async def _acall(
        self,
        inputs: dict[str, Any],
        run_manager: AsyncCallbackManagerForChainRun | None = None,
    ) -> dict[str, str]:
        return self._call(inputs, run_manager)

    @property
    def _chain_type(self) -> str:
        return "layer_videoclip_chain"


class VideoclipLayerAgent:
    def generate(
        self, project: AICPProject, shot: AICPShot,
        storyboard_artist: AICPStoryboardArtist
    ) -> AICPVideoLayer:
        """Generate an AICPVideoLayer for """
        # Call the chain and parse the resultA
        log_file = os.path.join(
            settings.AICP_OUTPUT_DIR, f"{project.id}", "logs", "layer_videoclip.log"
        )

        chain = LayerVideoclipChain(llm=llms.get_llm_instance("openai-gpt-4"),callbacks=[
                    FileCallbackHandler(filename=log_file),
                    StdOutCallbackHandler("green"),

                ], )
        result = chain.run({"text": shot.model_dump_json(indent=2)})
        # Parse the result
        parsed_result = json.loads(result)
        return AICPVideoLayer(
            id=str(uuid.uuid4()),
            prompt=parsed_result["prompt"],
            seed=project.seed,
            positive_prompt=storyboard_artist.positive_prompt,
            negative_prompt=storyboard_artist.negative_prompt,
            model=storyboard_artist.sd_model,
            width=project.production_config.video_width,
            height=project.production_config.video_height,
        )


        