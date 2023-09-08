import os

AICP_OUTPUT_DIR = os.environ.get("AICP_OUTPUT_DIR", os.path.join(os.path.dirname(__file__) , 'output'))
AICP_YAMLS_DIR = os.environ.get("AICP_YAMLS_DIR", os.path.join(os.path.dirname(__file__) , '..', 'yamls'))