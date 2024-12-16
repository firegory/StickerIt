from diffusers import AutoPipelineForText2Image
import torch
from io import BytesIO

class ImageGenerator():
    def __init__(self,
                 model_name: str = "kandinsky-community/kandinsky-2-1",
                 height: int = 512, width: int = 512,
                 negative_prompt= "low quality, bad quality"):
        self.pipe = AutoPipelineForText2Image.from_pretrained(model_name, torch_dtype=torch.float16)
        self.pipe.enable_model_cpu_offload()
        self.height, self.width = height, width
        self.negative_prompt = negative_prompt

    def generate(self, caption: str, chat_id: int) -> str:
        image = self.pipe(prompt=caption, negative_prompt=self.negative_prompt,
                          prior_guidance_scale=1.0,
                          height=self.height, width=self.width).images[0]
        torch.cuda.empty_cache()
        
        save_path = f'{chat_id}_sticker.webp'
        image.save(save_path)

        return save_path