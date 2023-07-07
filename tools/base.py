from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.tools import BaseTool
from typing import Optional
from models import Director, ProductionConfig


class AICPBaseTool(BaseTool):
    configured = False
    director: Optional[Director] = None
    production_config: Optional[ProductionConfig] = None
    actors: list[str] = []

    def set_config(
        self, director: Director, actors: list[str], config: ProductionConfig
    ):
        """Set the configuration for the tool"""
        self.director = director
        self.actors = actors
        self.production_config = config
        self.configured = True

    def initialize_agent(self):
        """Initialize the agent"""
        if not self.configured:
            raise Exception("Tool not configured. Please run set_config() first.")
