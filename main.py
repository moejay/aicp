from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from tools.researcher import ResearcherTool
from tools.script_writer import ScriptWriterTool

load_dotenv()
tools = [ResearcherTool(), ScriptWriterTool()]
llm = ChatOpenAI(temperature=0, streaming=True)
mrkl = initialize_agent(tools, llm, agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

topic = input("What topic do you want to make a video about?")

mrkl.run(f"""
1. Research {topic} using researcher tool.
2. Write a script using the scriptwriter tool.
        """)
