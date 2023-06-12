#!/usr/bin/env python

# ### Given a topic research the latest news

from typing import Optional, Type
import os
from dotenv import load_dotenv
load_dotenv()


from gpt4_openai import GPT4OpenAI

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain import LLMChain
from langchain.prompts.chat import (ChatPromptTemplate, SystemMessagePromptTemplate, AIMessagePromptTemplate, HumanMessagePromptTemplate)
from langchain.tools import BaseTool


class ResearcherTool(BaseTool):
    name = "researcher"
    description = "Useful when you need to research a topic"


    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        template = open("prompts/researcher.txt", "r").read()
        llm = GPT4OpenAI(token=os.environ["GPT4_TOKEN"], model='gpt-4-browsing', auto_continue=True)
        system_message_prompt = SystemMessagePromptTemplate.from_template(template)
        human_message_prompt = HumanMessagePromptTemplate.from_template("{text}")
        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
        chain = LLMChain(llm=llm, prompt=chat_prompt)

        result = chain.run(query)
        with open("research.txt", "w") as f:
            f.write(result)
        return "File written to research.txt"


    async def _arun(self, query:str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")

