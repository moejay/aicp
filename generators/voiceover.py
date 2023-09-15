import os
from generators.base import Generator
import soundfile as sf
from utils.voice_gen import generate_long_sentence_as_takes, save_audio_signal_wav, NEW_SAMPLE_RATE
import torch


class VoiceoverGenerator(Generator):
    def __init__(self):
        super().__init__()
        self.name = "Voiceover"
        self.processor = None
        self.model = None

    def load_model(self, **kwargs):
        if self.is_ready:
            return
        super().load_model(**kwargs)

    def generate(self, prompt: str, speaker: str, output_path: str, **kwargs):
        super().generate(prompt, output_path, **kwargs)
        #print(kwargs)
        #inputs = self.processor(prompt, voice_preset=kwargs["speaker"])
        #audio_array = self.model.generate(**inputs)
        #sr = self.model.generation_config.sample_rate
        #audio_to_save = audio_array.cpu().numpy().squeeze()
        #sf.write(output_path, audio_to_save, sr)
        audio_array= generate_long_sentence_as_takes(prompt, 
                                 speaker, 
                                 speech_wpm=75,
                                 output_dir=os.path.dirname(output_path),
                                 output_file_prefix="vo-take",
                                 text_temp=kwargs["speaker_text_temp"], 
                                 waveform_temp=kwargs["speaker_waveform_temp"])
        save_audio_signal_wav(audio_array, NEW_SAMPLE_RATE , output_path)

    def unload_model(self):
        if self.is_ready:
            torch.cuda.empty_cache()
        super().unload_model()
