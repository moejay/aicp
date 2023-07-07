#!/usr/bin/env python

# ### Given a topic research the latest news

from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from utils import utils, llms
from .base import AICPBaseTool


class ResearcherTool(AICPBaseTool):
    name = "researcher"
    description = "Useful when you need to research a topic"

    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""

        cast_member = self.director.get_researcher()
        chain = llms.get_llm(model=cast_member.model, template=cast_member.prompt)

        result = chain.run(query)
        with open(utils.RESEARCH, "w") as f:
            f.write(result)
        return f"File written to {utils.RESEARCH}"

    async def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")
