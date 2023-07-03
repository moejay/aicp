#!/usr/bin/env python

import os
import json
import logging

import yaml
from langchain.tools import BaseTool
from langchain import LLMChain
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.prompts.chat import (ChatPromptTemplate, SystemMessagePromptTemplate, AIMessagePromptTemplate, HumanMessagePromptTemplate, SystemMessage)

from .base import AICPBaseTool
from typing import Optional, Type
from utils import utils, llms, upload_yt

logger = logging.getLogger(__name__)

class YoutubeDistributorTool(AICPBaseTool):
    name = "youtubedistributor"
    description = "Useful for distributing videos to youtube"

    def ego(self):
        logger.info("Running ego")
        template = open("prompts/youtube_distributor.txt").read()
        chain = llms.get_llm(model=utils.get_config()["youtube_distributor"]["ego_model"], template=template)
        script_input = yaml.dump([{ "description": s["description"]} for s in utils.get_script()])

        response = chain.run(
            script_input
        )

        logger.info("Ego response: %s", response)
        return json.loads(response)
 


    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        ego_response = self.ego()
        print(ego_response)
        with open(utils.DISTRIBUTION_METADATA_FILE, "w") as file:
            file.write(json.dumps(ego_response))
#        upload_yt.upload_video(upload_yt.Options(
#            file=utils.FINAL_VIDEO_FILE,
#            title=ego_response["title"],
#            description=ego_response["description"],
#            tags=",".join(ego_response["tags"]),
#            privacy_status="private"
#            ))
#
        return "Done uploading video file to youtube, check your channel"

    def _arun(self, query:str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        raise NotImplementedError("Async not implemented")
