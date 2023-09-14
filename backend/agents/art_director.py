"""This is where the we make an outline from a script."""
from __future__ import annotations
import json
import os
import uuid

from langchain.prompts.base import StringPromptValue
from langchain.callbacks.file import FileCallbackHandler
from langchain.callbacks.stdout import StdOutCallbackHandler
from tenacity import retry, stop_after_attempt
from backend import settings
from backend.agents.layer_videoclip import VideoclipLayerAgent
from backend.agents.layer_voiceover import LayerVoiceoverAgent
from backend.models import (
    AICPActor,
    AICPProject,
    AICPScript,
    AICPOutline,
    AICPSequence,
    AICPScene,
    AICPShot,
    AICPStoryboardArtist,
)
from typing import Any
from backend.utils import llms

from pydantic import Extra

from langchain.schema.language_model import BaseLanguageModel
from langchain.callbacks.manager import (
    AsyncCallbackManagerForChainRun,
    CallbackManagerForChainRun,
)
from langchain.chains.base import Chain


class ArtDirectorChain(Chain):
    """
    Generates a video outline based on a script.
    """

    tmp_path: str = "/tmp"
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
        return ["project", "script", "storyboard_artist", "cast"]

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
        storyboard_artist = AICPStoryboardArtist.model_validate(inputs["storyboard_artist"])
        cast: dict[str, AICPActor] = inputs["cast"]

        outline = AICPOutline(id=project.id)
        for seq_idx, sequence in enumerate(script.sequences, start=1):
            if os.path.exists(os.path.join(self.tmp_path, f"seq-{seq_idx}.json")):
                outline.sequences.append(AICPSequence.model_validate(json.load(open(os.path.join(self.tmp_path, f"seq-{seq_idx}.json")))))

            sequence_json_dump = sequence.model_dump_json(indent=2)
            summary_input = f"""
            In the context of the following program:
            title: {project.program.title}
            description: {project.program.description}  

            Summarize this sequence in a few sentences, highlight the main points, mood, and tone, and any key moments:
            {sequence_json_dump}
            """
            seq_summary = self.llm.generate_prompt(
                [StringPromptValue(text=summary_input)],
                callbacks=run_manager.get_child() if run_manager else None,
            ).generations[0][0].text

            seq = AICPSequence(id=uuid.uuid4().__str__(), summary=seq_summary)
            # TODO Choose to reuse sequence or not
            outline.sequences.append(seq)

            for scene_idx, scene in enumerate(sequence.scenes, start=1):
                if os.path.exists(os.path.join(self.tmp_path, f"seq-{seq_idx}-scene-{scene_idx}.json")):
                    seq.scenes.append(AICPScene.model_validate(json.load(open(os.path.join(self.tmp_path, f"seq-{seq_idx}-scene-{scene_idx}.json")))))
                    continue
                scn = AICPScene(id=uuid.uuid4().__str__())
                # Summarize the scene
                scene_json_dump = scene.model_dump_json(indent=2)
                summary_input = f"""
                Summarize this scene in one or two sentences:
                {scene_json_dump}
                """
                scn_summary = self.llm.generate_prompt(
                            [
                            StringPromptValue(text=summary_input)
                            ], callbacks=run_manager.get_child() if run_manager else None,
                )
                if run_manager:
                    run_manager.on_text(scn_summary.generations[0][0].text)
                scn.summary = scn_summary.generations[0][0].text

                # Split the scene into shots
                split_input = f"""
                You are an art director for the following program:
                title: {project.program.title}
                description: {project.program.description}

                You are tasked with splitting the following scene into shots
                {scene_json_dump}

                You may have shots without dialog. If so, please leave the dialog line and character blank.

                return the results in the following format:
                [
                    {{
                        "title": "shot1",
                        "description": "shot1 description",
                        "artistic_direction": "shot1 artistic direction",
                        "dialog_line": "shot1 dialog line",
                        "dialog_character": "shot1 dialog character",
                    }}
                ]
                """
                @retry(stop=stop_after_attempt(5))
                def gen():
                    if run_manager:
                        run_manager.on_text(f"Generating shots for scene {scene_idx} in sequence {seq_idx}")
                        run_manager.on_text(split_input)
                    split_result = self.llm.generate_prompt(
                        [StringPromptValue(text=split_input)],
                        callbacks=run_manager.get_child() if run_manager else None,
                    )
                    if run_manager:
                        run_manager.on_text(split_result.generations[0][0].text)
                    split_result = json.loads(split_result.generations[0][0].text)
                    shots = []
                    for r in split_result:
                        r["id"] = uuid.uuid4().__str__()
                        r["layers"] = []
                        shots.append(AICPShot.model_validate(r))
                    return shots
                
                scn.shots = gen()
                seq.scenes.append(scn)
                with open(os.path.join(self.tmp_path, f"seq-{seq_idx}-scene-{scene_idx}.json"), "w") as f:
                    f.write(scn.model_dump_json(indent=2))
            
            with open(os.path.join(self.tmp_path, f"seq-{seq_idx}.json"), "w") as f:
                f.write(seq.model_dump_json(indent=2))

        # Enumerate sequences, scenes, and shots
        # Let's generate the layers for each of them starting with the sequence
        # We pass the updated outline to the next bit, so what gets generated is taken 
        # into account when generating the layers for the next bit
        # for example:
        # Generate layers for sequence 1 (which apply to all scenes and shots in sequence 1)
        # Generate layers for scene 1 (which apply to all shots in scene 1)
        # Generate layers for shot 1 (which apply to all layers in shot 1)
        # Generate layers for shot 2 (which apply to all layers in shot 2)
        # Generate layers for scene 2 (which apply to all shots in scene 2)
        # Generate layers for shot 1 (which apply to all layers in shot 1)
        # Generate layers for shot 2 (which apply to all layers in shot 2)
        # Generate layers for shot 3 (which apply to all layers in shot 3)
        # Generate layers for sequence 2 (which apply to all scenes and shots in sequence 2)
        # etc...
        
        for sequence in outline.sequences:
            for scene in sequence.scenes:
                for shot in scene.shots:
                    shot.layers = [] # Clear the layers
                    shot.layers.append(VideoclipLayerAgent().generate(project, shot, storyboard_artist))
                    if shot.dialog_character in cast.keys():
                        shot.layers.append(LayerVoiceoverAgent().generate(project, shot, cast=cast))


        return {self.output_key: outline.model_dump_json(indent=2)}

    async def _acall(
        self,
        inputs: dict[str, Any],
        run_manager: AsyncCallbackManagerForChainRun | None = None,
    ) -> dict[str, str]:
        return self._call(inputs, run_manager)

    @property
    def _chain_type(self) -> str:
        return "art_director_chain"


class ArtDirectorAgent:
    def generate(self, 
                 project: AICPProject, 
                 script: AICPScript, 
                 cast: dict[str, AICPActor],
                 storyboard_artist: AICPStoryboardArtist) -> AICPOutline:
        """Generate an outline from a script."""
        log_file = os.path.join(
            settings.AICP_OUTPUT_DIR, f"{project.id}", "logs", "art_director.log"
        )
        tmp_dir = os.path.join(settings.AICP_OUTPUT_DIR, f"{project.id}", "tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        parsed = json.loads(
            ArtDirectorChain(verbose=True, tmp_path=tmp_dir, llm=llms.get_llm_instance("openai-gpt-4")).run(
                {"project": project, "script": script, "storyboard_artist": storyboard_artist, "cast": cast},
                callbacks=[
                    FileCallbackHandler(filename=log_file),
                    StdOutCallbackHandler("green"),
                ],
            )
        )
        return AICPOutline.model_validate(parsed)
