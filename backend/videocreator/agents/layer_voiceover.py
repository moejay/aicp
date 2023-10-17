"""This is where we make voiceover layers for the clop."""
from __future__ import annotations
import json
import os
import uuid
from langchain.callbacks.file import FileCallbackHandler
from langchain.callbacks.stdout import StdOutCallbackHandler
from langchain.prompts.base import StringPromptValue
from tenacity import retry, stop_after_attempt, wait_fixed
from django.conf import settings

from videocreator.schema import (
    AICPClip,
    AICPProject,
    AICPScript,
    AICPOutline,
    AICPSequence,
    AICPScene,
    AICPShot,
    AICPActor,
    AICPVideoLayer,
    AICPStoryboardArtist,
    AICPVoiceoverLayer,
)
from videocreator.utils import llms, parsers
from typing import Any

from pydantic import Extra

from langchain.schema.language_model import BaseLanguageModel
from langchain.callbacks.manager import (
    AsyncCallbackManagerForChainRun,
    CallbackManagerForChainRun,
)
from langchain.chains.base import Chain


class LayerVoiceoverChain(Chain):
    """
    Generates a voiceover layer based on a script.
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
        return ["text", "actor", "character"]

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
        character = inputs["character"]
        actor = AICPActor.model_validate(inputs["actor"])

        input_value = f"""
        You are the actor {actor.name}.
        Your physical description is {actor.physical_description}.
        Your bio is {actor.bio}.

        You are playing the character {character}.

        Given the following information about the shot you are about to record:
        {text}

        Read the dialog_line how you think the character would say it in the style of the actor.
        
        Make sure you return the result in the following JSON format:
        {{
            "prompt": "The voiceover line said in the style of the actor."
        }}

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
        return "layer_voiceover_chain"


class LayerVoiceoverAgent:
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def generate(
        self, project: AICPProject, shot: AICPShot, cast: dict[str, AICPActor]
    ) -> AICPVoiceoverLayer:
        """Generate an AICPVideoLayer for"""
        # Call the chain and parse the resultA
        log_file = os.path.join(
            settings.AICP_OUTPUT_DIR, f"{project.id}", "logs", "layer_voiceover.log"
        )

        actor = cast[shot.dialog_character]
        chain = LayerVoiceoverChain(
            llm=llms.get_llm_instance("openai-gpt-4"),
            callbacks=[
                FileCallbackHandler(filename=log_file),
                StdOutCallbackHandler("green"),
            ],
        )

        result = chain.run(
            {
                "text": shot.model_dump_json(indent=2),
                "actor": actor,
                "character": shot.dialog_character,
            }
        )
        parsed_result = json.loads(result)
        return AICPVoiceoverLayer(
            id=str(uuid.uuid4()),
            prompt=parsed_result["prompt"],
            speaker=cast[shot.dialog_character].speaker,
            speaker_text_temp=cast[shot.dialog_character].speaker_text_temp,
            speaker_waveform_temp=cast[shot.dialog_character].speaker_waveform_temp,
        )
