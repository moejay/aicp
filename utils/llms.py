import os
import logging
from langchain import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from typing import Any, List, Mapping, Optional
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
from revChatGPT.V1 import Chatbot

logger = logging.getLogger(__name__)


class RevGPTLLM(LLM):
    model: str
    chatbot: Optional[Chatbot] = None

    @property
    def _llm_type(self) -> str:
        return "revgpt"

    def _get_chatbot(self) -> Chatbot:
        if self.chatbot is None:
            self.chatbot = Chatbot(
                config={
                    "access_token": os.environ["GPT4_TOKEN"],
                    "model": self.model,
                }
            )
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


def get_llm_instance(model, **kwargs):
    """Return an LLM instance based on the model.
    The general pattern is {model-prefix}-{model}
    The prefix defines what sort of class to use, such as ChatOpenAI or RevGPTLLM etc..
    """
    model_prefix_to_class = {
        "revgpt": RevGPTLLM,
        "openai": ChatOpenAI,
    }

    model_prefix = model.split("-")[0]
    if model_prefix not in model_prefix_to_class:
        raise ValueError(f"Unknown model prefix {model_prefix}")
    model_name = "-".join(model.split("-")[1:])

    logger.info(f"Using model {model_name} with prefix {model_prefix}")

    return model_prefix_to_class[model_prefix](model=model_name, **kwargs)


def get_llm(model, template, **kwargs):
    system_message_prompt = SystemMessagePromptTemplate.from_template(template)
    human_message_prompt = HumanMessagePromptTemplate.from_template("{input}")

    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )

    chain = LLMChain(llm=get_llm_instance(model, **kwargs), prompt=chat_prompt)
    return chain
