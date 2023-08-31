from generators.base import Generator
from transformers import AutoProcessor, BarkModel

class Voiceover(Generator):
    def __init__(self):
        super().__init__()
        self.name = "Voiceover"
        self.processor = None
        self.model = None

    def load_model(self, **kwargs):
        self.processor = AutoProcessor.from_pretrained("suno/bark")
        self.model = BarkModel.from_pretrained("suno/bark")

    def generate(self, **kwargs):
        inputs = self.processor(kwargs["text"], voice_preset=kwargs["voice_preset"])
        audio_array = self.model.generate(**inputs)
        sr = self.model.generation_config.sample_rate
        return audio_array.cpu().numpy().squeeze(), sr

        
    def unload_model(self):
        self.processor = None
        self.model = None
