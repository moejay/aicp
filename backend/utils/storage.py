"""Storage function module."""

import os

def write_file(file_path, file_contents):
    """Write file to path."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        f.write(file_contents)

def read_file(file_path):
    """Read file from path."""
    with open(file_path, "r") as f:
        return f.read()