"""This is where the research happens."""

import os
from backend import settings
from backend.models import AICPProject, AICPResearch
from backend.utils import llms
from utils import parsers

from langchain.callbacks.file import FileCallbackHandler
from langchain.callbacks.stdout import StdOutCallbackHandler


class ScriptAgent:
    def __init__(self, model, template):
        self.model = model
        self.template = template
        self.chain = llms.get_llm(model=model, template=template)

    def generate(self, project: AICPProject, research: AICPResearch):
        log_file = os.path.join(
            settings.AICP_OUTPUT_DIR, f"{project.id}", "logs", "script_writer.log"
        )
        prompt_params = parsers.get_params_from_prompt(self.template)
        params = {}
        for param in prompt_params:
            params[param] = parsers.resolve_param_from_video(
                video=project, param_name=param
            )
        params["input"] = research.result
        result = self.chain.run(
            **params,
            callbacks=[
                FileCallbackHandler(filename=log_file),
                StdOutCallbackHandler("green"),
            ],
        )
        return result
