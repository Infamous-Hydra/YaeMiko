# CREATED BY: https://t.me/O_oKarma
# API CREDITS: @Qewertyy
# PROVIDED BY: https://github.com/Team-ProjectCodeX

# <============================================== IMPORTS =========================================================>
import asyncio

import aiohttp
from telethon import events

from Mikobot import tbot as client

# <=======================================================================================================>

BASE_URL = "https://lexica.qewertyy.me"
SESSION_HEADERS = {"Host": "lexica.qewertyy.me"}


# <=============================================== CLASS + FUNCTION ========================================================>
class AsyncClient:
    def __init__(self):
        self.url = BASE_URL
        self.session = aiohttp.ClientSession()

    async def generate(self, model_id, prompt, negative_prompt):
        data = {
            "model_id": model_id,
            "prompt": prompt,
            "negative_prompt": negative_prompt if negative_prompt else "",
            "num_images": 1,
        }
        try:
            async with self.session.post(
                f"{self.url}/models/inference", data=data, headers=SESSION_HEADERS
            ) as resp:
                return await resp.json()
        except Exception as e:
            print(f"Request failed: {str(e)}")

    async def get_images(self, task_id, request_id):
        data = {"task_id": task_id, "request_id": request_id}
        try:
            async with self.session.post(
                f"{self.url}/models/inference/task", data=data, headers=SESSION_HEADERS
            ) as resp:
                return await resp.json()
        except Exception as e:
            print(f"Request failed: {str(e)}")


async def generate_image_handler(event, model_id):
    command_parts = event.text.split(" ", 1)
    if len(command_parts) < 2:
        await event.reply("Please provide a prompt.")
        return

    prompt = command_parts[1]
    negative_prompt = ""

    # Send the initial "Generating your image, wait sometime" message
    reply_message = await event.reply("Generating your image, please wait...")

    client = AsyncClient()
    response = await client.generate(model_id, prompt, negative_prompt)
    task_id = response["task_id"]
    request_id = response["request_id"]

    while True:
        generated_images = await client.get_images(task_id, request_id)

        if "img_urls" in generated_images:
            for img_url in generated_images["img_urls"]:
                # Delete the initial reply message
                await reply_message.delete()

                # Send the generated image
                await event.reply(file=img_url)
            break  # Exit the loop when images are available
        else:
            # Wait for a few seconds before checking again
            await asyncio.sleep(5)

        # Optionally, you can add a timeout to avoid an infinite loop
        timeout_seconds = 600  # 10 minutes (adjust as needed)
        if timeout_seconds <= 0:
            await reply_message.edit("Image generation timed out.")
            break

        timeout_seconds -= 5  # Decrement timeout by 5 seconds


@client.on(events.NewMessage(pattern=r"/meinamix"))
async def meinamix_handler(event):
    await generate_image_handler(event, model_id=2)


@client.on(events.NewMessage(pattern=r"/sushi"))
async def darksushi_handler(event):
    await generate_image_handler(event, model_id=7)


@client.on(events.NewMessage(pattern=r"/meinahentai"))
async def meinahentai_handler(event):
    await generate_image_handler(event, model_id=8)


@client.on(events.NewMessage(pattern=r"/darksushimix"))
async def darksushimix_handler(event):
    await generate_image_handler(event, model_id=9)


@client.on(events.NewMessage(pattern=r"/anylora"))
async def anylora_handler(event):
    await generate_image_handler(event, model_id=3)


@client.on(events.NewMessage(pattern=r"/cetusmix"))
async def cetusmix_handler(event):
    await generate_image_handler(event, model_id=10)


@client.on(events.NewMessage(pattern=r"/darkv2"))
async def darkv_handler(event):
    await generate_image_handler(event, model_id=14)


@client.on(events.NewMessage(pattern=r"/creative"))
async def creative_handler(event):
    await generate_image_handler(event, model_id=12)


# <================================================ END =======================================================>
