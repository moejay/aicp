SHELL=/usr/bin/env bash
PROJECT_NAME=aicp
BRANCH_NAME=$(shell if [ -z $$BRANCH_NAME ]; then git symbolic-ref -q --short HEAD; else echo $$BRANCH_NAME; fi)
PUBLIC_KEY=$(shell cat $$HOME/.ssh/id_ed25519.pub)
DOCKER_REPO=jwmarshall
CHATGPT_BASE_URL=http://127.0.0.1:9090/api/

export GRADIO_ANALYTICS_ENABLED=0

ifneq (,$(wildcard .env))
	OPENAI_API_KEY=$(shell cat .env | grep OPENAI_API_KEY | cut -d'=' -f2)
	GPT4_TOKEN=$(shell cat .env | grep GPT4_TOKEN | cut -d'=' -f2)
	RUNPOD_TEMPLATE=$(shell cat .env | grep RUNPOD_TEMPLATE | cut -d'=' -f2)
endif

export CHATGPT_BASE_URL

export CMAKE_ARGS="-DLLAMA_CUBLAS=on"
export FORCE_CMAKE=1

setup: bin/runpodctl python-deps docker-deps models/llama2_7b_chat_uncensored.bin

venv:
	@echo "Setting up Python virtual environment..."
	@if [ ! -d "venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m virtualenv venv; \
	fi

models:
	@mkdir -p models

models/llama2_7b_chat_uncensored.bin: models
	@wget -q https://huggingface.co/TheBloke/llama2_7b_chat_uncensored-GGML/resolve/main/llama2_7b_chat_uncensored.ggmlv3.q8_0.bin \
		-O models/llama2_7b_chat_uncensored.bin

bin/runpodctl:
	@echo "Installing runpodctl..."
	@mkdir -p bin
	@wget -O bin/runpodctl https://github.com/runpod/runpodctl/releases/download/v1.10.0/runpodctl-linux-amd
	@chmod +x bin/runpodctl

python-deps: venv
	@echo "Installing dependencies..."
	@venv/bin/pip install -r requirements.txt --upgrade

docker-deps:
	@echo "Building docker images..."
	@docker-compose build

docker-compose:
	@echo "Launching docker stack..."
	@docker-compose up -d

docker-gfpgan:
	@echo "Building GFPGAN container, this will take a while..."
	@docker build -t gfpgan -f dockerfiles/GFPGAN.Dockerfile dockerfiles

docker-kbe:
	@echo "Building KBE container, this will take a while..."
	@docker build -t ken-burns-effect -f dockerfiles/ken-burns-effect.Dockerfile dockerfiles

docker-image:
	@docker build --network=host -t $(PROJECT_NAME):$(BRANCH_NAME) .

docker-tag:
	@docker tag $(PROJECT_NAME):$(BRANCH_NAME) $(DOCKER_REPO)/$(PROJECT_NAME):$(BRANCH_NAME)

docker-push: docker-tag
	@docker push $(DOCKER_REPO)/$(PROJECT_NAME):$(BRANCH_NAME)

docker-vendor: docker-gfpgan docker-kbe 

notebook:
	@echo "Starting Jupyter Notebook..."
	@venv/bin/python -m jupyter notebook

video:
	@echo "Starting AI Content Producer..."
	@venv/bin/python main.py $(ARGS)

ui:
	@echo "Starting UI..."
	@venv/bin/python main.py --ui

dev:
	@echo "Starting development server..."
	@venv/bin/gradio main.py --ui

commentator:
	@echo "Starting Commentator..."
	@venv/bin/python commentator.py

auto:
	@echo "Starting AI Content Producer..."
	@/bin/bash auto.sh inputs.txt

rsync:
	@echo "Syncing files to remote server..."
	@gsutil -m rsync -r ./output gs://aicp-outputs/outputs

clean:
	@echo "Deleting virtualenv..."
	@rm -rf venv

runpod-create:
	@./bin/runpodctl create pod \
		--name $(PROJECT_NAME):$(BRANCH_NAME) \
		--secureCloud \
		--templateId $(RUNPOD_TEMPLATE) \
		--ports 7860/http \
		--ports 22/tcp \
		--containerDiskSize 40 \
		--volumeSize 100 \
		--volumePath /output \
		--gpuCount 1 \
		--gpuType 'NVIDIA RTX A4000' \
		--mem 20 \
		--vcpu 6 \
		--imageName $(DOCKER_REPO)/$(PROJECT_NAME):$(BRANCH_NAME) \
		--env PUBLIC_KEY="$(PUBLIC_KEY)" \
		--env CHATGPT_BASE_URL="$(CHATGPT_BASE_URL)" \
		--env OPENAI_API_KEY="$(OPENAI_API_KEY)" \
		--env GPT4_TOKEN="$(GPT4_TOKEN)"

runpod-rsync:
	@rsync -avz -e "ssh -p $(RUNPOD_PORT)" --progress root@$(RUNPOD_HOST):/output/* output/

check-format:
	@venv/bin/black . --check -v

reformat:
	@venv/bin/black .
