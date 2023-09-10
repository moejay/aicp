"""This is where the we make an outline from a script."""
from __future__ import annotations
import uuid

from langchain.chat_models import ChatOpenAI
from backend.models import AICPProject, AICPScript, AICPOutline, AICPSequence, AICPScene, AICPShot 
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
from langchain.prompts.base import BasePromptTemplate


class ArtDirectorChain(Chain):
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
        return ["project", "script"]

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

        project = AICPProject.model_validate(inputs["project"])
        script = AICPScript.model_validate(inputs["script"])
        outline = AICPOutline(id=project.id)
        for sequence in script.sequences:
            seq = AICPSequence(id=uuid.uuid4())
            # TODO Summarize the sequence
            # TODO Define the theme of the sequence, the input also includes the director template
            # TODO Define the mood of the sequence
            # TODO Define the tone of the sequence
            # TODO Choose to reuse sequence or not
            outline.sequences.append(seq)
            for scene in sequence.scenes:
                scn = AICPScene(id=uuid.uuid4())
                # TODO Summarize the scene
                # TODO Split the scene into shots
                # TODO Define the theme of the scene
                # TODO Define the mood of the scene
                # TODO Define the tone of the scene
                # TODO Choose to reuse scene or not
                seq.scenes.append(scn)

        response = self.llm.generate_prompt(
            [],
            callbacks=run_manager.get_child() if run_manager else None,
        )

        # If you want to log something about this run, you can do so by calling
        # methods on the `run_manager`, as shown below. This will trigger any
        # callbacks that are registered for that event.
        if run_manager:
            run_manager.on_text("Log something about this run")

        return {self.output_key: response.generations[0][0].text}

    async def _acall(
        self,
        inputs: dict[str, Any],
        run_manager: AsyncCallbackManagerForChainRun | None = None,
    ) -> dict[str, str]:
        return self._call(inputs, run_manager)
        
    @property
    def _chain_type(self) -> str:
        return "art_director_chain"
