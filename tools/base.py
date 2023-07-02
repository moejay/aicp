from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool
from typing import Optional, Type
from utils.utils import ProgramConfig


class AICPBaseTool(BaseTool):

    configured = False
    config: Optional[ProgramConfig] = None
    
    def set_config(self, config: ProgramConfig):
        """ Set the configuration for the tool """
        self.config = config
        self.configured = True

    def initialize_agent(self):
        """ Initialize the agent """
        if not self.configured:
            raise Exception("Tool not configured. Please run set_config() first.")


