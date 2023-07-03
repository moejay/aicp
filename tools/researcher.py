#!/usr/bin/env python

# ### Given a topic research the latest news

from typing import Optional, Type
import os
from dotenv import load_dotenv
load_dotenv()

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain import LLMChain
from langchain.prompts.chat import (ChatPromptTemplate, SystemMessagePromptTemplate, AIMessagePromptTemplate, HumanMessagePromptTemplate)
from langchain.tools import BaseTool
from utils import utils, llms
from .base import AICPBaseTool

class ResearcherTool(AICPBaseTool):
    name = "researcher"
    description = "Useful when you need to research a topic"


    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        template = open("prompts/researcher.txt", "r").read()
        chain = llms.get_llm(model=utils.get_config()["researcher"]["model"], template=template)

        result = chain.run(query)
        with open(utils.RESEARCH, "w") as f:
            f.write(result)
        return "File written to research.txt"


    async def _arun(self, query:str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")

