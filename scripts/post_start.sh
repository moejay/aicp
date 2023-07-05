#!/usr/bin/env bash

# run proxy in background
ChatGPTProxy &

# Start AICP
cd /workspace && python3 main.py
