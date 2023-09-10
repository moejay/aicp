"""This is where the research happens."""

from backend.models import AICPProject, AICPResearch
from backend.utils import llms
from utils import parsers

class ScriptAgent():

    def __init__(self, model, template):
        self.model = model
        self.template = template
        self.chain = llms.get_llm(model=model, template=template)

    def generate(self, project: AICPProject, research: AICPResearch):
        prompt_params = parsers.get_params_from_prompt(self.template)
        params = {}
        for param in prompt_params:
            params[param] = parsers.resolve_param_from_video(
                video=project, param_name=param
            )
        params["input"] = research.result 
        result = self.chain.run(
            **params,
        )
        return result




