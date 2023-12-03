# CREATED BY: @Qewertyy

# <============================================== IMPORTS =========================================================>
import os
import traceback

from pyrogram import Client, filters
from pyrogram import types as t

from Mikobot import app
from Mikobot.state import state

from .telegraph import telegraph, upload_file


# <================================================ FUNCTIONS =====================================================>
@app.on_message(filters.command(["p", "pp", "reverse", "sauce"]))
async def reverseImageSearch(_: Client, m: t.Message):
    try:
        reply = await m.reply_text("`Downloading...`")
        file = None
        if not m.reply_to_message:
            return await reply.edit("Reply to an image?")
        if m.reply_to_message.document is False or m.reply_to_message.photo is False:
            return await reply.edit("Reply to an image?")
        if (
            m.reply_to_message.document
            and m.reply_to_message.document.mime_type
            in ["image/png", "image/jpg", "image/jpeg"]
            or m.reply_to_message.photo
        ):
            if (
                m.reply_to_message.document
                and m.reply_to_message.document.file_size > 5242880
            ):
                return await reply.edit("Reply to an image?")
            file = await m.reply_to_message.download()
        else:
            return await reply.edit("Reply to an image?")
        await reply.edit("`Uploading to the server...`")
        imgUrl = upload_file(file)
        os.remove(file)
        if imgUrl is None:
            return await reply.edit("Ran into an error.")
        output = await reverse_image_search("google", f"https://graph.org/{imgUrl[0]}")
        if output is None:
            return await reply.edit("Ran into an error.")

        names = output["content"]["bestResults"]["names"]
        urls = output["content"]["bestResults"]["urls"]
        btn = t.InlineKeyboardMarkup(
            [[t.InlineKeyboardButton(text="IMAGE URL", url=urls[-1])]]
        )

        if len(names) > 10:
            message = "\n".join(
                [f"{index+1}. {name}" for index, name in enumerate(names[:10])]
            )
            htmlMessage = f"<br/>".join(
                [f"{index+1}. {name}" for index, name in enumerate(names)]
            )
            htmlMessage += "<br/><br/><h3>URLS</h3><br/>"
            htmlMessage += f"<br/>".join([f"{url}" for url in urls])
            htmlMessage += (
                "<br/><br/>By <a href='https://lexica.qewertyy.me'>LexicaAPI</a>"
            )
            telegraph_page = telegraph.create_page(
                "More Results", html_content=htmlMessage
            )
            message += f"\n\n[More Results](https://telegra.ph/{telegraph_page['path']})\n\nBy @LexicaAPI"
            await reply.delete()
            return await m.reply_text(message, reply_markup=btn)

        message = "\n".join([f"{index+1}. {name}" for index, name in enumerate(names)])
        await reply.delete()
        await m.reply_text(f"{message}\n\nBy @LexicaAPI", reply_markup=btn)
    except Exception as E:
        traceback.print_exc()
        return await m.reply_text("Ran into an error.")


async def reverse_image_search(search_engine, img_url) -> dict:
    try:
        response = await state.post(
            f"https://reverse.qewertyy.me/image-reverse/{search_engine}?img_url={img_url}",
        )
        if response.status_code != 200:
            return None
        output = response.json()
        if output["code"] != 2:
            return None
        return output
    except Exception as E:
        raise Exception(f"API Error: {E}")


# <=================================================== HELP ====================================================>


__help__ = """
🖼 *IMAGE REVERSE*

» `/p`, `/pp`, `/reverse`, `/sauce`: Reverse image search using various search engines.

➠ *Usage:*
Reply to an image with one of the above commands to perform a reverse image search.

➠ *Example:*
» `/p` - Perform a reverse image search.

➠ *Note:*
- Supported image formats: PNG, JPG, JPEG.
- Maximum file size: 5 MB.
"""

__mod_name__ = "REVERSE"
# <================================================ END =======================================================>
