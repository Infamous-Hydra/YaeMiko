# <============================================== IMPORTS =========================================================>
import asyncio
import html
import json
import re
from typing import Optional

import requests
from telegram import (
    CallbackQuery,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    User,
)
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden, RetryAfter
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.helpers import mention_html

import Database.sql.kuki_sql as sql
from Mikobot import function
from Mikobot.plugins.log_channel import gloggable

# <=======================================================================================================>


# <================================================ FUNCTION =======================================================>
@gloggable
async def kukirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query: Optional[CallbackQuery] = update.callback_query
    user: Optional[User] = update.effective_user
    if match := re.match(r"rm_chat\((.+?)\)", query.data):
        user_id = match[1]
        chat: Optional[Chat] = update.effective_chat
        if is_kuki := sql.rem_kuki(chat.id):
            sql.rem_kuki(user_id)
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"AI_DISABLED\n"
                f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            )
        else:
            await update.effective_message.edit_text(
                f"Chatbot disable by {mention_html(user.id, user.first_name)}.",
                parse_mode=ParseMode.HTML,
            )

    return ""


@gloggable
async def kukiadd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query: Optional[CallbackQuery] = update.callback_query
    user: Optional[User] = update.effective_user
    if match := re.match(r"add_chat\((.+?)\)", query.data):
        user_id = match[1]
        chat: Optional[Chat] = update.effective_chat
        if is_kuki := sql.set_kuki(chat.id):
            sql.set_kuki(user_id)
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"AI_ENABLE\n"
                f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            )
        else:
            await update.effective_message.edit_text(
                f"Hey Darling Chatbot enable by {mention_html(user.id, user.first_name)}.",
                parse_mode=ParseMode.HTML,
            )

    return ""


@gloggable
async def kuki(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.effective_user
    message = update.effective_message
    msg = "Choose an option"
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(text="Enable", callback_data="add_chat({})")],
            [InlineKeyboardButton(text="Disable", callback_data="rm_chat({})")],
        ]
    )
    await message.reply_text(
        msg,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


async def kuki_message(context: ContextTypes.DEFAULT_TYPE, message):
    reply_message = message.reply_to_message
    if message.text.lower() == "kuki":
        return True
    if reply_message:
        if reply_message.from_user.id == (await context.bot.get_me()).id:
            return True
    else:
        return False


async def chatbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.effective_user
    message = update.effective_message
    chat_id = update.effective_chat.id
    bot = context.bot
    is_kuki = sql.is_kuki(chat_id)
    if not is_kuki:
        return

    if message.text and not message.document:
        if not await kuki_message(context, message):
            return
        Message = message.text
        await bot.send_chat_action(chat_id, action="typing")
        kukiurl = requests.get(
            f"http://api.brainshop.ai/get?bid=176809&key=lbMN8CXTGzhn1NKG&uid=[user]&msg={Message}"
        )

        Kuki = json.loads(kukiurl.text)
        kuki = Kuki["cnt"]

        await asyncio.sleep(0.3)
        await message.reply_text(kuki)


async def list_all_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chats = sql.get_all_kuki_chats()
    text = "<b>Neko Enabled Chats</b>\n"
    for chat in chats:
        try:
            x = await context.bot.get_chat(int(*chat))
            name = x.title or x.first_name
            text += f"• <code>{name}</code>\n"
        except (BadRequest, Forbidden):
            sql.rem_kuki(*chat)
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after)
    await update.effective_message.reply_text(text, parse_mode="HTML")


# <=================================================== HELP ====================================================>


__help__ = """
➠ *Admins only command*:

» /chatbot: shows chatbot panel.
"""

__mod_name__ = "CHATBOT"


# <================================================ HANDLER =======================================================>
CHATBOTK_HANDLER = CommandHandler("chatbot", kuki, block=False)
ADD_CHAT_HANDLER = CallbackQueryHandler(kukiadd, pattern=r"add_chat", block=False)
RM_CHAT_HANDLER = CallbackQueryHandler(kukirm, pattern=r"rm_chat", block=False)
CHATBOT_HANDLER = MessageHandler(
    filters.TEXT
    & (~filters.Regex(r"^#[^\s]+") & ~filters.Regex(r"^!") & ~filters.Regex(r"^\/")),
    chatbot,
    block=False,
)
LIST_ALL_CHATS_HANDLER = CommandHandler("allchats", list_all_chats, block=False)

function(ADD_CHAT_HANDLER)
function(CHATBOTK_HANDLER)
function(RM_CHAT_HANDLER)
function(LIST_ALL_CHATS_HANDLER)
function(CHATBOT_HANDLER)

__handlers__ = [
    ADD_CHAT_HANDLER,
    CHATBOTK_HANDLER,
    RM_CHAT_HANDLER,
    LIST_ALL_CHATS_HANDLER,
    CHATBOT_HANDLER,
]
# <================================================ END =======================================================>
