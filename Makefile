SHELL=/usr/bin/env bash
CHATGPT_BASE_URL=http://127.0.0.1:9090/api/

export CHATGPT_BASE_URL


setup: python-deps docker-deps

venv:
	@echo "Setting up Python virtual environment..."
	@if [ ! -d "venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m virtualenv venv; \
	fi

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
	@docker build -t gfpgan -f dockerfiles/GFPGAN.Dockerfile .

docker-kbe:
	@echo "Building KBE container, this will take a while..."
	@docker build -t ken-burns-effect -f dockerfiles/ken-burns-effect.Dockerfile .

docker-vendor: docker-gfpgan docker-kbe 

notebook: docker-compose
	@echo "Starting Jupyter Notebook..."
	@venv/bin/python -m jupyter notebook

video: docker-compose 
	@echo "Starting AI Content Producer..."
	@venv/bin/python main.py

rsync:
	@echo "Syncing files to remote server..."
	@gsutil -m rsync -r ./output gs://aicp-outputs/outputs

clean:
	@echo "Deleting virtualenv..."
	@rm -rf venv
