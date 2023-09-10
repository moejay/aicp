"""This is where we assign the actors to the script."""
from __future__ import annotations
import json
import uuid

from langchain import PromptTemplate
from langchain.prompts.base import StringPromptValue 
 
from backend.models import AICPProject, AICPScript, AICPOutline, AICPSequence, AICPScene, AICPShot , AICPActor
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
from langchain.schema.prompt import PromptValue


class CastingDirectorChain(Chain):
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
        return ["project", "script", "actors"]

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
        actors = project.actors if len(project.actors) > 0 else [AICPActor.model_validate(actor) for actor in inputs["actors"]]
        # Get all characters in the script, put them in a set, and add two of their lines
        characters = dict()
        for sequence in script.sequences:
            for scene in sequence.scenes:
                for line in scene.lines:
                    if line.character not in characters:
                        characters[line.character] = [line.line]
                    elif len(characters[line.character]) < 2:
                        characters[line.character].append(line.line)
                
        # Given the characters and lines, assign actors to characters
        # Ask the llm to do that, and return it in JSON format
        actors_string = [f"{actor.name}: {actor.physical_description}, {actor.bio}\n" for actor in actors]
        input_value = f"""You are a casting director, your job is to assign available actors to the characters in the script.
                Here are the available actors, physical descriptions and their bios:
                {actors_string}
                Here are the characters and their lines:
                {characters}
                Please assign the actors to the characters in the script.
                use the following format:
                {{
                    "actor_name": ["character1", "character2"],
                    "other_actor_name": ["character3", "character4"]
                }}"""
        result = self.llm.generate_prompt(
            [
               StringPromptValue (text=input_value)
            ], callbacks=run_manager.get_child() if run_manager else None,
        )
        if run_manager:
            run_manager.on_text(result.generations[0][0].text)
        casting_result = json.loads(result.generations[0][0].text)

        return {self.output_key: result.generations[0][0].text}

    async def _acall(
        self,
        inputs: dict[str, Any],
        run_manager: AsyncCallbackManagerForChainRun | None = None,
    ) -> dict[str, str]:
        return self._call(inputs, run_manager)
        
    @property
    def _chain_type(self) -> str:
        return "casting_director_chain"


class CastingDirectorAgent():

    def generate(self, project: AICPProject, script: AICPScript, actors: list[AICPActor]) -> dict[str, str]:
        chain = CastingDirectorChain(llm=llms.get_llm_instance("openai-gpt-4"))
        return chain.run({"project": project, "script": script, "actors": project.actors})