import logging
import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler

logger = logging.getLogger(__name__)


def get_pipeline_with_loras(
    base_model_path, checkpoint_path: str | list[str] | None = None
) -> StableDiffusionPipeline:
    """Get a StableDiffusionPipeline with zero or more loras loaded."""

    pipeline = StableDiffusionPipeline.from_pretrained(
        base_model_path,
        torch_dtype=torch.float16,
        safety_checker=None,
    )
    pipeline.to("cuda")
    pipeline.enable_xformers_memory_efficient_attention()
    pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
        pipeline.scheduler.config, use_karras_sigmas=True
    )
    pipeline.scheduler.config.algorithm_type = "sde-dpmsolver++"
    if checkpoint_path is None:
        return pipeline
    if isinstance(checkpoint_path, list):
        for path in checkpoint_path:
            pipeline.load_lora_weights(path)
    else:
        pipeline.load_lora_weights(checkpoint_path)

    return pipeline
