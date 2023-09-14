import os
import logging
from langchain import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.callbacks.stdout import StdOutCallbackHandler
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.llms import LlamaCpp
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


MODEL_PREFIX_TO_CLASS = {
    "revgpt": RevGPTLLM,
    "openai": ChatOpenAI,
    "llama": LlamaCpp,
}


def get_llm_instance(model, **kwargs):
    """Return an LLM instance based on the model.
    The general pattern is {model-prefix}-{model}
    The prefix defines what sort of class to use, such as ChatOpenAI or RevGPTLLM etc..
    """

    model_prefix = model.split("-")[0]
    if model_prefix not in MODEL_PREFIX_TO_CLASS:
        raise ValueError(f"Unknown model prefix {model_prefix}")
    model_name = "-".join(model.split("-")[1:])

    logger.info(f"Using model {model_name} with prefix {model_prefix}")
    model_args = {}
    if model_prefix == "revgpt":
        model_args["model"] = model_name
    elif model_prefix == "openai":
        model_args["model"] = model_name
    elif model_prefix == "llama":
        model_args["model_path"] = os.path.join("models", f"{model_name}.bin")
        model_args["n_ctx"] = 4096
        model_args["n_gpu_layers"] = 20
        model_args["n_batch"] = 512

    model_args.update(kwargs)

    return MODEL_PREFIX_TO_CLASS[model_prefix](**model_args)


def get_llm(model, template, **kwargs):
    system_message_prompt = SystemMessagePromptTemplate.from_template(template)
    human_message_prompt = HumanMessagePromptTemplate.from_template("{input}")

    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )

    chain = LLMChain(llm=get_llm_instance(model, **kwargs), prompt=chat_prompt, callbacks=kwargs.pop("callbacks", [
                StdOutCallbackHandler("green"),
    ]), verbose=True)
    return chain


AVAILABLE_MODELS = [
    "revgpt-gpt4",
    "openai-gpt4",
    "openai-gpt-3.5",
    "openai-gpt-3.5-turbo-16k",
    "llama-llama2_7b_chat_uncensored",
]
