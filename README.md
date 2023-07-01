## 🎥 AI Makes videos

Given some prompt, the AI will end up creating a video "suitable" for YouTube/Rumble


## 🕵️ Agent Roadmap 

[X] 🔍 Research Agent

[X] ✍️  Script Writer Agent

[X] 🔉 Voiceover Artist Agent

[X] 🖼️ Storyboard Artist Agent

[X] - Music Composer Agent

[X] - Sound Engineer Agent

[X] 📦 Producer Agent

[ ] 🎬 Director Agent

[/] 📦 Distributor Agent

## Installation and Running


* create .env file and put `OPENAI_API_KEY` and `GPT4_TOKEN` variables in it

* Make sure you got python and virtualenv installed
* `make setup`
* `make proxy` to run the chatgpt-proxy 

Then you can run either
* `make notebook` will launch jupyter
* `make video` is to run the whole thing, you will be asked to provide the topic to search


## Agent description

Each of the agents should have a notebook associated with it, and how it's created.

### 🔍 Research Agent 

This agent will research the topic obviously.

### ✍️  Script Writer Agent

This agent will write the script based on the research done by Research Agent.

### 🔉 Voiceover Artist Agent

This agent will rewrite the script lines in their own words according to their character bio and create the audio voice lines.

### 🖼️ Storyboard Artist Agent

This agent will rewrite the scene descriptions as text-to-image prompts and create X images per scene.

### - Music Composer Agent

This agent will rewrite the scene descriptions into prompts for text-to-music models.

### - Sound Engineer Agent

This agent assembles the audio components into a single wav file.

### - Producer Agent

This agent assembles the audio and visual components of into the final video file.

### 📦 Distributor Agent

This agent will provide the title, description, and tags for the video

### 📹 Video Creator Agent [Future]

This agent will create video clips to be used instead of just image
