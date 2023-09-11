from abc import ABC, abstractmethod


class Generator(ABC):
    def __init__(self):
        self.name = "Generator"

    @abstractmethod
    def load_model(self, **kwargs):
        """Loads the model for the generator"""

    @abstractmethod
    def generate(self, **kwargs):
        """Run the generation"""

    @abstractmethod
    def unload_model(self):
        """Unload the model"""
