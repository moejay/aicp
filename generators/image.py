
import torch
from generators.base import Generator
from utils import image_gen


class ImageGenerator(Generator):
    def __init__(self):
        super().__init__()
        self.name = "Image"
        self.model = None
        self.pipe = None

    def load_model(self, **kwargs):
        self.model = kwargs["model"] 
        self.pipe = image_gen.get_pipeline_with_loras(base_model_path=self.model)
        super().load_model(**kwargs)

    def generate(self,
                 prompt: str,
                 output_path: str,
                 negative_prompt: str = "",
                 seed: int = 0,
                 width: int = 512,
                 height: int = 512,
                 **kwargs):
        super().generate(prompt, output_path, **kwargs)
        # settings
        guidance_scale = 7.5 # Magic numbers
        num_inference_steps = 50 # Magic numbers
        
        images = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_inference_steps=num_inference_steps,
            num_images_per_prompt=1,
            guidance_scale=guidance_scale,
        ).images

        # Save image
        images[0].save(output_path)


    def unload_model(self):
        if self.is_ready:
            self.model = None
            self.pipe = None
            del self.pipe
            torch.cuda.empty_cache()
        super().unload_model()

