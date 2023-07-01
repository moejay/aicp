#!/usr/bin/env python

import os
import json
import logging

import yaml
from langchain.tools import BaseTool
from langchain import LLMChain
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.prompts.chat import (ChatPromptTemplate, SystemMessagePromptTemplate, AIMessagePromptTemplate, HumanMessagePromptTemplate, SystemMessage)

from typing import Optional, Type
from utils import utils, llms, upload_yt

logger = logging.getLogger(__name__)

class YoutubeDistributorTool(BaseTool):
    name = "youtubedistributor"
    description = "Useful for distributing videos to youtube"

    def ego(self):
        logger.info("Running ego")
        llm = llms.RevGPTLLM(model=utils.get_config()["youtube_distributor"]["ego_model"])

        template = open("prompts/youtube_distributor.txt").read()
        system_message_prompt = SystemMessage(content=template)
        human_message_prompt = HumanMessagePromptTemplate.from_template("{script}")

        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

        chain = LLMChain(llm=llm, prompt=chat_prompt) 
        script_input = yaml.dump([{ "description": s["description"]} for s in utils.get_script()])

        response = chain.run(
            script=script_input
        )

        logger.info("Ego response: %s", response)
        return json.loads(response)
 


    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        ego_response = self.ego()
        print(ego_response)
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
