SHELL=/usr/bin/env bash


setup:
	@echo "Setting up Python virtual environment"
	@if [ ! -d "venv" ]; then \
		echo "Creating virtual environment"; \
		python3 -m virtualenv venv; \
	fi
	@echo "Installing dependencies"
	@venv/bin/pip install -r requirements.txt
	@echo "Done"

notebook: setup
	@echo "Starting Jupyter Notebook"
	@venv/bin/python -m jupyter notebook

video: setup
	@echo "Starting AI Content Producer"
	@venv/bin/python main.py
