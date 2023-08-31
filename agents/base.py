from langchain.agents import AgentType
from langchain.agents import initialize_agent

class BaseAgent():
    _TOOLS = []
    _LLM = None
    def __init__(self):
        self._agent_chain = initialize_agent(
            self._TOOLS, 
            self._LLM, 
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION, 
            verbose=True, 
        )

    def generate(self, prompt):
        return self._agent_chain.run(input=prompt)
