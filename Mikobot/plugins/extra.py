# <============================================== IMPORTS =========================================================>
from time import gmtime, strftime, time

from pyrogram import filters
from pyrogram.types import Message
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from Mikobot import LOGGER, app, function
from Mikobot.plugins.helper_funcs.chat_status import check_admin

# <=======================================================================================================>

UPTIME = time()  # Check bot uptime


# <================================================ FUNCTION =======================================================>
async def getid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    your_id = update.message.from_user.id
    message_id = update.message.message_id
    reply = update.message.reply_to_message

    text = f"[Message ID:](https://t.me/{chat.username}/{message_id}) `{message_id}`\n"
    text += f"[Your ID:](tg://user?id={your_id}) `{your_id}`\n"

    if context.args:
        try:
            user_id = context.args[0]
            text += f"[User ID:](tg://user?id={user_id}) `{user_id}`\n"
        except Exception:
            await update.message.reply_text(
                "This user doesn't exist.", parse_mode="Markdown"
            )
            return

    text += f"[Chat ID:](https://t.me/{chat.username}) `{chat.id}`\n\n"

    if reply:
        text += f"[Replied Message ID:](https://t.me/{chat.username}/{reply.message_id}) `{reply.message_id}`\n"
        text += f"[Replied User ID:](tg://user?id={reply.from_user.id}) `{reply.from_user.id}`\n\n"

    if reply and reply.forward_from_chat:
        text += f"The forwarded channel, {reply.forward_from_chat.title}, has an id of `{reply.forward_from_chat.id}`\n\n"

    if reply and reply.sender_chat:
        text += f"ID of the replied chat/channel, is `{reply.sender_chat.id}`"

    # Sticker ID to be sent
    sticker_id = (
        "CAACAgIAAx0CanzPTAABASPCZQdU9NbQIol5TW1GU2zV4KfjDMEAAnccAALIWZhJPyYLf3FzPHswBA"
    )

    # Send the sticker
    await update.message.reply_sticker(sticker=sticker_id)

    # Send the text message as a caption
    await update.message.reply_text(
        text, parse_mode="Markdown", disable_web_page_preview=True
    )


# Function to handle the "logs" command
@check_admin(only_dev=True)
async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    with open("Logs.txt", "rb") as f:
        caption = "Here is your log"
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Close", callback_data="close")]]
        )
        message = await context.bot.send_document(
            document=f,
            filename=f.name,
            caption=caption,
            reply_markup=reply_markup,
            chat_id=user.id,
        )

        # Store the message ID for later reference
        context.user_data["log_message_id"] = message.message_id


# Asynchronous callback query handler for the "close" button
@check_admin(only_dev=True)
async def close_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    message_id = context.user_data.get("log_message_id")
    if message_id:
        await context.bot.delete_message(
            chat_id=query.message.chat_id, message_id=message_id
        )


@app.on_message(filters.command("pyroping"))
async def ping(_, m: Message):
    LOGGER.info(f"{m.from_user.id} used ping cmd in {m.chat.id}")
    start = time()
    replymsg = await m.reply_text(text="Pinging...", quote=True)
    delta_ping = time() - start

    up = strftime("%Hh %Mm %Ss", gmtime(time() - UPTIME))
    image_url = "https://telegra.ph/file/f215a1c4adf25a5bad81b.jpg"

    # Send the image as a reply
    await replymsg.reply_photo(
        photo=image_url,
        caption=f"<b>Pyro-Pong!</b>\n{delta_ping * 1000:.3f} ms\n\nUptime: <code>{up}</code>",
    )
    await replymsg.delete()


# <=======================================================================================================>


# <================================================ HANDLER =======================================================>
function(CommandHandler("logs", logs, block=False))
function(CommandHandler("id", getid, block=False))
function(CallbackQueryHandler(close_callback, pattern="^close$", block=False))

# <================================================= HELP ======================================================>
__help__ = """
➠ *Commands*:

» /instadl, /insta <link>: Get instagram contents like reel video or images.

» /pyroping: see pyroping.

» /hyperlink <text> <link> : Creates a markdown hyperlink with the provided text and link.

» /pickwinner <participant1> <participant2> ... : Picks a random winner from the provided list of participants.

» /id: reply to get user id.
"""

__mod_name__ = "EXTRA"
# <================================================ END =======================================================>
