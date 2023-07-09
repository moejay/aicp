#!/usr/bin/env bash

# run proxy in background
ChatGPTProxy &

# Start AICP
ln -s /output /workspace/output
cd /workspace && python3 main.py --ui
