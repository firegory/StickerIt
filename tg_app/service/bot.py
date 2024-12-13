import tritonclient.http.aio as httpclient
from tritonclient.utils import InferenceServerException
import tokenizers
import numpy as np
import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import Command, CommandStart
from aiogram.utils import executor
from aiogram.types import Message

import logging

logging.basicConfig(filename="bot.log", level=logging.INFO)
logger = logging.getLogger("bot")

TRITON_HOST = os.environ["TRITON_ADDRESS"]

triton_client = None

async def get_triton_client():
    global triton_client
    if triton_client is None:
        triton_client = httpclient.InferenceServerClient(url=TRITON_HOST, verbose=True)
    return triton_client

tokenizer = tokenizers.Tokenizer.from_file("/service/tokenizer/tokenizer/tokenizer.json")

with open("/service/tokenizer/id2label.json", "r") as f:
    id2label = list(zip(*sorted(json.load(f).items(), key=lambda x: int(x[0]))))[1]

with open("/service/tokenizer/label2desc.json", "r") as f:
    label2desc = json.load(f)

async def call_roberta(text: str, model_name: str) -> list[float]:
    logger.info(f"{model_name} call")
    tokens = tokenizer.encode(text)
    input_ids = np.array(tokens.ids, dtype=np.int64)[None, :]
    attention_masks = np.array(tokens.attention_mask, dtype=np.int64)[None, :]

    inputs = []
    input = httpclient.InferInput("input_ids", list(input_ids.shape), "INT64")
    input.set_data_from_numpy(input_ids)
    inputs.append(input)

    input = httpclient.InferInput("attention_masks", list(attention_masks.shape), "INT64")
    input.set_data_from_numpy(attention_masks)
    inputs.append(input)

    output = httpclient.InferRequestedOutput("outputs")

    try:
        client = await get_triton_client()
        results = await client.infer(
            model_name=model_name,
            inputs=inputs,
            outputs=[output],
        )
        return id2label[np.argmax(results.as_numpy("outputs")[0])]
    except InferenceServerException as e:
        logger.error(e)
        print(e)
        return None

token = os.environ["BOT_TOKEN"]
bot = Bot(token=token)
dp = Dispatcher(bot)

@dp.message_handler(CommandStart())
async def process_start_command(message: Message):
    logger.info(f"Start pressed by {message.from_user.id}")
    await message.answer(
        'Начало работы\n\n'
        'Доступные команды можно посмотреть по команде - /help'
    )

@dp.message_handler(Command(commands="help"))
async def process_help_command(message: Message):
    logger.info(f"Help pressed by {message.from_user.id}")
    await message.answer(
        'Напиши любой текст на английском, а я расскажу о твоих намерениях\n\n/intents получить список интентов размера 151💀\n\n/desc <intent> получить описание интента'
    )

@dp.message_handler(Command(commands="intents"))
async def process_intents_command(message: Message):
    logger.info(f"Intents pressed by {message.from_user.id}")
    await message.answer("\n".join(id2label))

@dp.message_handler(Command(commands="desc"))
async def process_intents_command(message: Message):
    logger.info(f"Desc pressed by {message.from_user.id}")
    msg_split = message.text.split(" ")
    
    if len(msg_split) != 2:
        await message.answer("/desc <intent> получить описание интента")
    else:
        intent = msg_split[1]     
        if intent in label2desc:
            await message.answer(label2desc[intent])
        else:
            await message.answer(f"Такого интента не существует {intent}")

@dp.message_handler()
async def answer(message: types.Message):
    logger.info(f"Message {message.text} from {message.from_user.id}")
    out = await call_roberta(message.text, "dirty_roberta")
    if out is None:
        out = "KAL"
    out2 = await call_roberta(message.text, "clean_roberta")
    if out2 is None:
        out2 = "KAL"
    answer = f"Dirty RoBERTa:\nintent: {out}\nClean RoBERTa:\nintent: {out2}"
    await message.answer(answer)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
