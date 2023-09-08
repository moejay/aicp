from langchain.tools import BaseTool
from backend.models import Video, Director, ProductionConfig, Actor


class AICPBaseTool(BaseTool):
    video: Video
