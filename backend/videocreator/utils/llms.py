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

logger = logging.getLogger(__name__)

MODEL_PREFIX_TO_CLASS = {
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
    if model_prefix == "openai":
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

    chain = LLMChain(
        llm=get_llm_instance(model, **kwargs),
        prompt=chat_prompt,
        callbacks=kwargs.pop(
            "callbacks",
            [
                StdOutCallbackHandler("green"),
            ],
        ),
        verbose=True,
    )
    return chain


AVAILABLE_MODELS = [
    "openai-gpt4",
    "openai-gpt-3.5",
    "openai-gpt-3.5-turbo-16k",
    "llama-llama2_7b_chat_uncensored",
]
