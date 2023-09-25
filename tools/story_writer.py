#!/usr/bin/env python

import os
from typing import Optional
from dotenv import load_dotenv
import logging
import yaml

load_dotenv()

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from utils import utils, llms, parsers

from .base import AICPBaseTool

logger = logging.getLogger(__name__)


class StoryWriterTool(AICPBaseTool):
    name = "storywriter"
    description = (
        "Useful when you need to write a story or treatment, pass the file containing the research"
    )

    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        cast_member = self.video.director.get_story_writer()
        chain = llms.get_llm(model=cast_member.model, template=cast_member.prompt)

        prompt_params = parsers.get_params_from_prompt(cast_member.prompt)
        prompt_params.append("input")
        # This is in addition to the input (Human param)
        # Resolve params from existing config/director/program
        params = {}
        for param in prompt_params:
            params[param] = parsers.resolve_param_from_video(
                video=self.video, param_name=param
            )
        params["input"] = open(utils.RESEARCH, "r").read()

        result = chain.run(**params)

        with open(utils.STORY, "w") as f:
            f.write(result)

        # Summarize the story in a few sentences
        if not os.path.exists(utils.STORY_SUMMARY):
            with open(utils.STORY_SUMMARY, "w") as f:
                f.write(
                    llms.get_llm(
                        model=cast_member.model,
                        template="Summarize the following story in 4 sentences",
                    ).run(result)
                )

        return f"File written to {utils.STORY}"

    def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")
