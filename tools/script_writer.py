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


class ScriptWriterTool(AICPBaseTool):
    name = "scriptwriter"
    description = (
        "Useful when you need to write a script, pass the file containing the research"
    )

    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        # Check if script is already generated, if so, just return
        if os.path.exists(utils.SCRIPT):
            return f"File already exists at {utils.SCRIPT}"
        cast_member = self.video.director.get_script_writer()
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

        retries = 3
        while retries > 0:
            try:
                result = chain.run(
                    **params,
                )
                parsed = yaml.load(result, Loader=yaml.Loader)
                # Make sure that every element in the list has the following:
                # title, description, an array of characters (with name and actor name)
                # an array of dialogue that includes

                with open(utils.SCRIPT, "w") as f:
                    f.write(result)
                # Summarize the script in a few sentences
                if not os.path.exists(utils.SCRIPT_SUMMARY):
                    with open(utils.SCRIPT_SUMMARY, "w") as f:
                        f.write(
                            llms.get_llm(
                                model=cast_member.model,
                                template="Summarize the following script in 4 sentences",
                            ).run(result)
                        )

                return f"File written to {utils.SCRIPT}"
            except Exception as e:
                retries -= 1
                logger.warning(f"{e}")
                logger.warning("Failed to generate script, retrying")

        logger.error("Failed to generate script, retries exhausted")

        return "Failed to generate script"

    def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")
