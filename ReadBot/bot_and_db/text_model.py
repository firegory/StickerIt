from unsloth import FastLanguageModel
import torch

class CaptionGenerator():
    def __init__(self,
                 max_seq_length: int=2048,
                 dtype=None, load_in_4bit: bool=True,
                 model_name: str="Eka-Korn/Qwen-2.5_SFT_v3"):

        self.alpaca_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

            ### Instruction:
            {}

            ### Input:
            {}

            ### Response:
            {}"""
        self.instruction = "based on the Russian dialogue from chat, generate a description in English for further generation of a sticker that would be best suited in this situation."
        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name = model_name,
            max_seq_length = max_seq_length,
            dtype = dtype,
            load_in_4bit = load_in_4bit,
        )
        FastLanguageModel.for_inference(self.model)
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

    def generate(self, context: str) -> str:
        inputs = self.tokenizer(
        [
            self.alpaca_prompt.format(
                self.instruction,
                context,
                "", # output - leave this blank for generation!
            )
        ], return_tensors = "pt").to(self.device)

        outputs = self.model.generate(**inputs, max_new_tokens = 64, use_cache = True)
        generated_caption = self.tokenizer.batch_decode(outputs)[0]
        response_index, end_index = generated_caption.find("Response:"), generated_caption.find("<|endoftext|>")
        extracted_text = generated_caption[response_index + len("Response:"):end_index].strip()
        
        return extracted_text