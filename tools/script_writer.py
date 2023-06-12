#!/usr/bin/env python

import os
from typing import Optional, Type

from dotenv import load_dotenv
load_dotenv()


from gpt4_openai import GPT4OpenAI

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain import LLMChain
from langchain.prompts.chat import (ChatPromptTemplate, SystemMessagePromptTemplate, AIMessagePromptTemplate, HumanMessagePromptTemplate)
from langchain.tools import BaseTool

class ScriptWriterTool(BaseTool):
    name = "scriptwriter"
    description = "Useful when you need to write a script, pass the file containing the research"

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        template = open("prompts/scriptwriter.txt", "r").read()
        llm = GPT4OpenAI(token=os.environ["GPT4_TOKEN"], model='gpt-4-scriptwriter', auto_continue=True)
        system_message_prompt = SystemMessagePromptTemplate.from_template(template)
        human_message_prompt = HumanMessagePromptTemplate.from_template("{text}")
        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
        chain = LLMChain(llm=llm, prompt=chat_prompt)
        research_text = open("research.txt", "r").read()
        result = chain.run(research_text)
        with open("script.txt", "w") as f:
            f.write(result)
        return "File written to script.txt"

    def _arun(self, query:str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")
