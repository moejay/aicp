#!/usr/bin/env python

from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from utils import utils, llms

from .base import AICPBaseTool
class ScriptWriterTool(AICPBaseTool):
    name = "scriptwriter"
    description = "Useful when you need to write a script, pass the file containing the research"

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        cast_member = self.director.get_script_writer()
        chain = llms.get_llm(model=cast_member.model, template=cast_member.prompt)

        research_text = open(utils.RESEARCH, "r").read()
        result = chain.run(research_text)
        with open(utils.SCRIPT, "w") as f:
            f.write(result)
        return f"File written to {utils.SCRIPT}"

    def _arun(self, query:str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")
