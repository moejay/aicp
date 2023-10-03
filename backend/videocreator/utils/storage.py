"""Storage function module."""
from pydantic import BaseModel
import yaml
import os


def write_file(file_path, file_contents: str | BaseModel):
    """Write file to path."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        if isinstance(file_contents, BaseModel):
            f.write(yaml.safe_dump(file_contents.model_dump()))
        else:
            f.write(file_contents)


def read_file(file_path):
    """Read file from path."""
    with open(file_path, "r") as f:
        return f.read()
