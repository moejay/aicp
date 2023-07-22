#!/usr/bin/env bash

# Bootstrap some dependancies/models
python3 -c "import nltk;nltk.download('punkt')"

# Start AICP
ln -s /output /workspace/output
cd /workspace && python3 main.py --ui
