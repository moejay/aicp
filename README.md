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
* `make ui` to run the webui to generate a video
* `make video` the command line to run a single input, pass as make args (env variables) eg: `ARGS=--prompt "prompt" --actors zane --director mvp_director --production-config default_config --program matrix --output some/output` 
* `make auto` will look for `inputs.txt` with `|` separated ( prompt | output_dir | actor ) 
can be used to run multiple back to back video creations

## The templates and yamls

* `cast` includes the actors/directors/researchers etc.. also includes the configs
* `programs` includes the well, programs aka shows

### The production config

The config currently includes the output video dimensions (also img2img dimension),
as well as the stable diffusion initial dimensions

### The director 

A Director is a collection of researcher, and other artists involved in the production
Each artist, can have multiple yamls that can be chosen as part of a director

### The actors

specify a list of actors to be part of the show
currently only shows with one actor are supported
this is still in heavy development for v0.69


### The program aka: show

Has a name and a description, not used anywhere currently


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

## Cloud hosted runner (WIP)

AICP can now be run in the cloud via Runpod.io

1. Install command line utility: `make bin/runpodctl`
2. Create Runpod.io API key: https://www.runpod.io/console/user/settings
3. Create `runpodctl` configuration: `./bin/runpodctl config --apiKey=YOUR_API_KEY`
4. Add Docker Hub login credentials to your RunPod account: https://www.runpod.io/console/user/settings
5. Create private template (required for private images):
	1. Click the burger menu when logged into RunPod
	2. Click on **My Templates** in the sidebar
	3. Click the **New Template** button at the top left
	4. Create the new template ensuring the following settings:
		1. The container image is the image name of your private image
		2. You select the appropriate Container Registry Credentials
		3. Set the container disk to 40GB at least
		4. Set the volume disk to be much larger, like 100GB
		5. Set the volume mount path to `/output`
		6. Expose 7860 HTTP port
		7. Expose 22 TCP Port
		8. Do not add any environment variables to the template, we will override them later anyway
	5. Copy the template ID into your .env `RUNPOD_TEMPLATE=your-template-id`
	6. Launch a new pod with `make runpod-create`

## Development

(to do- developer guide)

### Code Formatting

This project uses the `black` code formatter. You can check your local environment by running `make check-format` and you can autoformat your code with `make reformat`. See `pyproject.toml` for configuration.

Note: This code format is enforced for pull requests.
