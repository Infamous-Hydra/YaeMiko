import os
import uuid
from html import escape

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CommandHandler

from Mikobot import dispatcher

ENDPOINT = "https://sasta-api.vercel.app/googleImageSearch"


# Define strings
class STRINGS:
    REPLY_TO_MEDIA = "ℹ️ Please reply to a message that contains one of the supported media types, such as a photo, sticker, or image file."
    UNSUPPORTED_MEDIA_TYPE = "⚠️ <b>Unsupported media type!</b>\nℹ️ Please reply with a supported media type: image, sticker, or image file."

    REQUESTING_API_SERVER = "🫧"

    DOWNLOADING_MEDIA = "🔍"
    UPLOADING_TO_API_SERVER = "📤"
    PARSING_RESULT = "📥"

    EXCEPTION_OCCURRED = "❌Exception occurred!\n\n<b>Exception: {}"

    RESULT = """
Query: {query}
Google Page: <a href="{search_url}">Link</a>
    """
    OPEN_SEARCH_PAGE = "OPEN LINK"


# Define command handlers
async def reverse_image_search(update: Update, context: CallbackContext):
    message = update.message
    if len(message.text.split()) > 1:
        image_url = message.text.split()[1]
        params = {"image_url": image_url}
        status_msg = await message.reply_text(STRINGS.REQUESTING_API_SERVER)
        response = await requests.get(ENDPOINT, params=params)

    elif message.reply_to_message:
        reply = message.reply_to_message
        if reply.photo or reply.sticker or reply.document:
            status_msg = await message.reply_text(STRINGS.DOWNLOADING_MEDIA)
            file_path = f"temp/{uuid.uuid4()}"
            try:
                file_id = (
                    reply.photo[-1].file_id
                    if reply.photo
                    else (
                        reply.sticker.file_id
                        if reply.sticker
                        else reply.document.file_id
                    )
                )
                file = await context.bot.get_file(file_id)
                os.makedirs(
                    os.path.dirname(file_path), exist_ok=True
                )  # Ensure directory exists
                await file.download_to_drive(
                    file_path
                )  # Use download instead of download_to_drive
            except Exception as exc:
                text = STRINGS.EXCEPTION_OCCURRED.format(exc)
                await message.reply_text(text)
                return

            with open(file_path, "rb") as image_file:
                files = {"file": image_file}
                await status_msg.edit_text(STRINGS.UPLOADING_TO_API_SERVER)
                response = requests.post(ENDPOINT, files=files)

            os.remove(file_path)  # Remove the file after it's been used

    if response.status_code == 404:
        text = STRINGS.EXCEPTION_OCCURRED.format(response.json()["error"])
        await message.reply_text(text)
        await status_msg.delete()
        return
    elif response.status_code != 200:
        text = STRINGS.EXCEPTION_OCCURRED.format(response.text)
        await message.reply_text(text)
        await status_msg.delete()
        return

    await status_msg.edit_text(STRINGS.PARSING_RESULT)
    response_json = response.json()
    query = response_json["query"]
    search_url = response_json["search_url"]

    # Escape HTML tags in query to prevent them from being interpreted as markup
    escaped_query = escape(query)

    text = STRINGS.RESULT.format(
        query=(
            f"<code>{escaped_query}</code>"
            if escaped_query
            else "<i>Name not found</i>"
        ),
        search_url=search_url,
    )
    buttons = [[InlineKeyboardButton(STRINGS.OPEN_SEARCH_PAGE, url=search_url)]]
    await message.reply_text(
        text,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML,  # Specify parse_mode as 'HTML' to interpret HTML tags
    )
    await status_msg.delete()


dispatcher.add_handler(
    CommandHandler(["reverse", "pp", "p", "grs", "sauce"], reverse_image_search)
)
