# <============================================== IMPORTS =========================================================>
import os
from datetime import datetime

from PIL import Image
from pyrogram import filters
from telegraph import Telegraph, exceptions, upload_file

from Mikobot import app
from Mikobot.utils.errors import capture_err

# <=======================================================================================================>

TMP_DOWNLOAD_DIRECTORY = "tg-File/"
bname = "YaeMiko_Roxbot"  # ᴅᴏɴ'ᴛ ᴇᴅɪᴛ ᴛʜɪᴀ ʟɪɴᴇ
telegraph = Telegraph()
r = telegraph.create_account(short_name=bname)
auth_url = r["auth_url"]


# <================================================ FUNCTION =======================================================>
@app.on_message(filters.command(["tgm", "tmg", "telegraph"], prefixes="/"))
@capture_err
async def telegraph_upload(client, message):
    if message.reply_to_message:
        start = datetime.now()
        r_message = message.reply_to_message
        input_str = message.command[0]
        if input_str in ["tgm", "tmg", "telegraph"]:
            downloaded_file_name = await client.download_media(
                r_message, file_name=TMP_DOWNLOAD_DIRECTORY
            )
            end = datetime.now()
            ms = (end - start).seconds
            h = await message.reply_text(f"Downloaded to file in {ms} seconds.")
            if downloaded_file_name.endswith(".webp"):
                resize_image(downloaded_file_name)
            try:
                start = datetime.now()
                media_urls = upload_file(downloaded_file_name)
            except exceptions.TelegraphException as exc:
                await h.edit_text("Error: " + str(exc))
                os.remove(downloaded_file_name)
            else:
                end = datetime.now()
                ms_two = (end - start).seconds
                os.remove(downloaded_file_name)
                await h.edit_text(
                    f"""
➼ **Uploaded to [Telegraph](https://telegra.ph{media_urls[0]}) in {ms + ms_two} seconds.**\n 
➼ **Copy Link :** `https://telegra.ph{media_urls[0]}`""",
                    disable_web_page_preview=False,
                )
    else:
        await message.reply_text(
            "Reply to a message to get a permanent telegra.ph link."
        )


def resize_image(image):
    im = Image.open(image)
    im.save(image, "PNG")


# <=================================================== HELP ====================================================>
__help__ = """ 
➠ *TELEGRAPH*:

» /tgm, /tmg, /telegraph*:* `get telegram link of replied media`
 """

__mod_name__ = "TELEGRAPH"
# <================================================ END =======================================================>
