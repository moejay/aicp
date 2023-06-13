SHELL=/usr/bin/env bash


setup:
	@echo "Setting up Python virtual environment"
	@if [ ! -d "venv" ]; then \
		echo "Creating virtual environment"; \
		python3 -m virtualenv venv; \
	fi
	@echo "Installing dependencies"
	@venv/bin/pip install -r requirements.txt
	@echo "Build proxy docker"
	@docker build -t chatgpt-proxy -f ProxyDockerfile .
	@echo "Done"

notebook: 
	@echo "Starting Jupyter Notebook"
	@export CHATGPT_BASE_URL=http://localhost:9090/api/ && venv/bin/python -m jupyter notebook

proxy:
	@echo "Starting Proxy"
	@docker run -dp 9090:9090 chatgpt-proxy

video: 
	@echo "Starting AI Content Producer"
	@export CHATGPT_BASE_URL=http://localhost:9090/api/ && venv/bin/python main.py
