
from models import AICPVideo
from utils import llms, parsers

class Writer():

    def __init__(self, llm_model, prompt_template):
        self.model = llm_model
        self.prompt = prompt_template
        self.chain = llms.get_llm(model=self.model, template=self.prompt)
        
    def full_prompt(self, query) -> dict:
        prompt_params = parsers.get_params_from_prompt(self.prompt)
        # This is in addition to the input (Human param)
        # Resolve params from existing config/director/program
        params = {}
        for param in prompt_params:
            params[param] = parsers.resolve_param_from_video(
                video=self.video, param_name=param
            )
        return params

    def write(self, query) -> str:
        params["input"] = query
        result = self.chain.run(
            **params,
        )
        return result
