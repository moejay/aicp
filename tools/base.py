from langchain.tools import BaseTool
from models import Video, Director, ProductionConfig, Actor


class AICPBaseTool(BaseTool):
    video: Video
