import os
from langchain import LLMChain
from langchain.prompts.chat import (ChatPromptTemplate, SystemMessagePromptTemplate, AIMessagePromptTemplate, HumanMessagePromptTemplate)

from typing import Any, List, Mapping, Optional
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
from revChatGPT.V1 import Chatbot

class RevGPTLLM(LLM):
    model: str
    chatbot: Optional[Chatbot] = None

    @property
    def _llm_type(self) -> str:
        return "revgpt"

    def _get_chatbot(self) -> Chatbot:
        if self.chatbot is None:
            self.chatbot = Chatbot(config={
                "access_token": os.environ["GPT4_TOKEN"],
                "model": self.model,
            })
        return self.chatbot
    
    def _ask(self, prompt: str) -> str:
        response = ""
        for data in self._get_chatbot().ask(prompt, auto_continue=True):
                response = data["message"]
        return response

    def _call(
            self,
            prompt: str,
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            ) -> str:
        if stop is not None:
            raise NotImplementedError("Stop not implemented")
        return self._ask(prompt)


    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying params for the LLM."""
        return {
                "model": self.model,
        }
