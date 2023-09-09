"""This is where the research happens."""

from langchain.chat_models import ChatOpenAI
from agents.base import BaseAgent
from utils import llms, parsers

class ResearchAgent(BaseAgent):
    _LLM = ChatOpenAI()

    def __init__(self):
        cast_member = self.video.director.get_researcher()
        chain = llms.get_llm(model=cast_member.model, template=cast_member.prompt)
        prompt_params = parsers.get_params_from_prompt(cast_member.prompt)
        params = {}
        for param in prompt_params:
            params[param] = parsers.resolve_param_from_video(
                video=self.video, param_name=param
            )
        params["input"] = query
        result = chain.run(
            **params,
        )




