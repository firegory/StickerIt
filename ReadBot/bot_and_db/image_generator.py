from diffusers import AutoPipelineForText2Image
import torch

class ImageGenerator():
    def __init__(self,
                 model_name: str = "kandinsky-community/kandinsky-2-1",
                 height: int = 512, width: int = 512):
        self.pipe = AutoPipelineForText2Image.from_pretrained(model_name, torch_dtype=torch.float16)
        self.pipe.enable_model_cpu_offload()
        self.height, self.width = height, width
        self.negative_prompt = "low quality, bad quality"

    def generate(self, caption):
        image = self.pipe(prompt=caption, negative_prompt=self.negative_prompt,
                          prior_guidance_scale=1.0,
                          height=self.height, width=self.width).images[0]
        return image