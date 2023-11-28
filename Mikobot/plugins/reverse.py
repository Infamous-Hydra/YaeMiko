# Copyright 2023 Qewertyy, MIT License

import traceback,os
from pyrogram import Client,filters, types as t
from Mikobot import app
from .telegraph import upload_file,telegraph
import httpx

@app.on_message(filters.command(["pp","reverse","sauce"]))
async def reverseImageSearch(_: Client,m: t.Message):
    try:
        reply = await m.reply_text("`Downloading...`")
        file = None
        if not m.reply_to_message:
            return await reply.edit("Reply to an image?")
        if m.reply_to_message.document is False or m.reply_to_message.photo is False:
            return await reply.edit("Reply to an image?")
        if m.reply_to_message.document and m.reply_to_message.document.mime_type in ['image/png','image/jpg','image/jpeg'] or m.reply_to_message.photo:
            if m.reply_to_message.document and m.reply_to_message.document.file_size > 5242880:
                return await reply.edit("Reply to an image?")
            file = await m.reply_to_message.download()
        else:
            return await reply.edit("Reply to an image?")
        await reply.edit("`Uploading to the server...`")
        imgUrl = upload_file(file)
        os.remove(file)
        if imgUrl is None:
            return await reply.edit("Ran into an error.")
        output = await ReverseImageSearch("google",f"https://graph.org/{imgUrl[0]}")
        if output is None:
            return await reply.edit("Ran into an error.")
        message = ''
        names = output['content']['bestResults']['names']
        urls = output['content']['bestResults']['urls']
        btn = t.InlineKeyboardMarkup(
            [
                [
                    t.InlineKeyboardButton(text="Image URL",url=urls[-1])
                ]
            ])
        if len(names) > 10:
            message = "\n".join([f"{index+1}. {name}" for index, name in enumerate(names[:10])])
            htmlMessage = f"<br/>".join([f"{index+1}. {name}" for index, name in enumerate(names)])
            htmlMessage += "<br/><br/><h3>URLS</h3><br/>"
            htmlMessage += f"<br/>".join([f"{url}" for url in urls])
            htmlMessage += "<br/><br/>By <a href='https://lexica.qewertyy.me'>LexicaAPI</a>"
            url = telegraph.create_page("More Results",htmlMessage)
            message += f"\n\n[More Results]({url})\nBy @LexicaAPI"
            await reply.delete()
            return await m.reply_text(message,reply_markup=btn)
        message ="\n".join([f"{index+1}. {name}" for index, name in enumerate(output['content']['bestResults']['names'])])
        await reply.delete()
        await m.reply_text(f"{message}\n\nBy @LexicaAPI",reply_markup=btn)
    except Exception as E:
        traceback.print_exc()
        return await m.reply_text("Ran into an error.")

async def ReverseImageSearch(search_engine,img_url) -> dict:
    try:
        client = httpx.AsyncClient()
        response = await client.post(
            f"https://lexica.qewertyy.me/image-reverse/{search_engine}?img_url={img_url}",
        )
        if response.status_code != 200:
            return None
        output = response.json()
        if output['code'] != 2:
            return None
        return output
    except Exception as E:
        raise Exception(f"API Error: {E}")