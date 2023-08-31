"""This is where the research happens."""

from langchain.chat_models import ChatOpenAI
from agents.base import BaseAgent

class ResearchAgent(BaseAgent):
    _LLM = ChatOpenAI()

