from abc import ABC, abstractmethod


class Generator(ABC):
    def __init__(self):
        self.name = "Generator"
        self.is_ready = False

    @abstractmethod
    def load_model(self, **kwargs):
        """Loads the model for the generator"""
        self.is_ready = True

    @abstractmethod
    def generate(self, prompt: str, output_path: str, **kwargs):
        """Run the generation"""
        if not self.is_ready:
            raise Exception("Model not loaded")

    @abstractmethod
    def unload_model(self):
        """Unload the model"""
        self.is_ready = False
