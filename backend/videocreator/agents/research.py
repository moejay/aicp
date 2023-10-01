"""This is where the research happens."""

from langchain.chat_models import ChatOpenAI
from videocreator.schema import AICPProject
from videocreator.utils import llms
from videocreator.utils import parsers


class ResearchAgent:
    def __init__(self, model, template):
        self.model = model
        self.template = template
        self.chain = llms.get_llm(model=model, template=template)

    def generate(self, project: AICPProject, query):
        prompt_params = parsers.get_params_from_prompt(self.template)
        params = {}
        for param in prompt_params:
            params[param] = parsers.resolve_param_from_video(
                video=project, param_name=param
            )
        params["input"] = query
        result = self.chain.run(
            **params,
        )
        return result
