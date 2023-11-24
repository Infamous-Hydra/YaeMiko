# <============================================== IMPORTS =========================================================>
import asyncio
from io import BytesIO
from typing import Union

from pyrogram import Client
from pyrogram import filters as fil
from pyrogram.types import Message
from telegram import ChatMemberAdministrator, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden, TelegramError
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters
from telegram.helpers import escape_markdown

import Database.sql.users_sql as sql
from Database.sql.users_sql import get_all_users
from Mikobot import DEV_USERS, LOGGER, OWNER_ID, app, dispatcher, function

# <=======================================================================================================>

USERS_GROUP = 4
CHAT_GROUP = 5
DEV_AND_MORE = DEV_USERS.append(int(OWNER_ID))


# <================================================ FUNCTION =======================================================>
# get_arg function to retrieve an argument from a message
def get_arg(message):
    args = message.text.split(" ")
    if len(args) > 1:
        return args[1]
    else:
        return None


# Broadcast Function
@app.on_message(fil.command("gcast"))
async def broadcast_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    texttt = message.text.split(" ")

    if user_id not in [OWNER_ID] + DEV_USERS:
        await message.reply_text(
            "You are not authorized to use this command. Only the owner and authorized users can use it."
        )
        return

    if len(texttt) < 2:
        return await message.reply_text(
            "<b>GLOBALCASTING COMMANDS</b>\n-user : broadcasting all user's DM\n-group : broadcasting all groups\n-all : broadcasting both\nEx: /gcast -all"
        )

    if message.reply_to_message is None and not get_arg(message):
        return await message.reply_text(
            "<b>Please provide a message or reply to a message</b>"
        )

    tex = await message.reply_text("<code>Starting global broadcast...</code>")

    usersss = 0
    chatttt = 0
    uerror = 0
    cerror = 0
    chats = sql.get_all_chats() or []
    users = get_all_users()

    if "-all" in texttt:
        texttt.append("-user")
        texttt.append("-group")

    if "-user" in texttt:
        for chat in users:
            if message.reply_to_message:
                msg = message.reply_to_message
            else:
                msg = get_arg(message)
            try:
                if message.reply_to_message:
                    aa = await msg.copy(chat.user_id)
                else:
                    aa = await client.send_message(chat.user_id, msg)

                usersss += 1
                await asyncio.sleep(0.3)
            except Exception:
                uerror += 1
                await asyncio.sleep(0.3)
    if "-group" in texttt:
        for chat in chats:
            if message.reply_to_message:
                msg = message.reply_to_message
            else:
                msg = get_arg(message)
            try:
                if message.reply_to_message:
                    aa = await msg.copy(chat.chat_id)
                else:
                    aa = await client.send_message(chat.chat_id, msg)

                chatttt += 1
                await asyncio.sleep(0.3)
            except Exception:
                cerror += 1
                await asyncio.sleep(0.3)

    await tex.edit_text(
        f"<b>Message Successfully Sent</b> \nTotal Users: <code>{usersss}</code> \nFailed Users: <code>{uerror}</code> \nTotal GroupChats: <code>{chatttt}</code> \nFailed GroupChats: <code>{cerror}</code>"
    )


async def get_user_id(username: str) -> Union[int, None]:
    # ensure valid user ID
    if len(username) <= 5:
        return None

    if username.startswith("@"):
        username = username[1:]

    users = sql.get_userid_by_name(username)

    if not users:
        return None

    elif len(users) == 1:
        return users[0].user_id

    else:
        for user_obj in users:
            try:
                userdat = await dispatcher.bot.get_chat(user_obj.user_id)
                if userdat.username == username:
                    return userdat.id

            except BadRequest as excp:
                if excp.message == "Chat not found":
                    pass
                else:
                    LOGGER.exception("Error extracting user ID")

    return None


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    to_send = update.effective_message.text.split(None, 1)

    if len(to_send) >= 2:
        to_group = False
        to_user = False
        if to_send[0] == "/broadcastgroups":
            to_group = True
        if to_send[0] == "/broadcastusers":
            to_user = True
        else:
            to_group = to_user = True
        chats = sql.get_all_chats() or []
        users = get_all_users()
        failed = 0
        failed_user = 0
        if to_group:
            for chat in chats:
                try:
                    await context.bot.sendMessage(
                        int(chat.chat_id),
                        escape_markdown(to_send[1], 2),
                        parse_mode=ParseMode.MARKDOWN_V2,
                        disable_web_page_preview=True,
                    )
                    await asyncio.sleep(1)
                except TelegramError:
                    failed += 1
        if to_user:
            for user in users:
                try:
                    await context.bot.sendMessage(
                        int(user.user_id),
                        escape_markdown(to_send[1], 2),
                        parse_mode=ParseMode.MARKDOWN_V2,
                        disable_web_page_preview=True,
                    )
                    await asyncio.sleep(1)
                except TelegramError:
                    failed_user += 1
        await update.effective_message.reply_text(
            f"Broadcast complete.\nGroups failed: {failed}.\nUsers failed: {failed_user}.",
        )


async def log_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.effective_message

    sql.update_user(msg.from_user.id, msg.from_user.username, chat.id, chat.title)

    if msg.reply_to_message:
        sql.update_user(
            msg.reply_to_message.from_user.id,
            msg.reply_to_message.from_user.username,
            chat.id,
            chat.title,
        )

    if msg.forward_from:
        sql.update_user(msg.forward_from.id, msg.forward_from.username)


async def chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_chats = sql.get_all_chats() or []
    chatfile = "List of chats.\n0. Chat Name | Chat ID | Members Count\n"
    P = 1
    for chat in all_chats:
        try:
            curr_chat = await context.bot.getChat(chat.chat_id)
            await curr_chat.get_member(context.bot.id)
            chat_members = await curr_chat.get_member_count(context.bot.id)
            chatfile += "{}. {} | {} | {}\n".format(
                P,
                chat.chat_name,
                chat.chat_id,
                chat_members,
            )
            P = P + 1
        except:
            pass

    with BytesIO(str.encode(chatfile)) as output:
        output.name = "groups_list.txt"
        await update.effective_message.reply_document(
            document=output,
            filename="groups_list.txt",
            caption="Here be the list of groups in my database.",
        )


async def chat_checker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    try:
        bot_admin = await update.effective_message.chat.get_member(bot.id)
        if isinstance(bot_admin, ChatMemberAdministrator):
            if bot_admin.can_post_messages is False:
                await bot.leaveChat(update.effective_message.chat.id)
    except Forbidden:
        pass


def __user_info__(user_id):
    if user_id in [777000, 1087968824]:
        return """Groups Count: ???"""
    if user_id == dispatcher.bot.id:
        return """Groups Count: ???"""
    num_chats = sql.get_user_num_chats(user_id)
    return f"""Groups Count: {num_chats}"""


def __stats__():
    return f"• {sql.num_users()} users, across {sql.num_chats()} chats"


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


# <================================================ HANDLER =======================================================>
BROADCAST_HANDLER = CommandHandler(
    ["broadcastall", "broadcastusers", "broadcastgroups"], broadcast, block=False
)
USER_HANDLER = MessageHandler(
    filters.ALL & filters.ChatType.GROUPS, log_user, block=False
)
CHAT_CHECKER_HANDLER = MessageHandler(
    filters.ALL & filters.ChatType.GROUPS, chat_checker, block=False
)
CHATLIST_HANDLER = CommandHandler("groups", chats, block=False)

function(USER_HANDLER, USERS_GROUP)
function(BROADCAST_HANDLER)
function(CHATLIST_HANDLER)
function(CHAT_CHECKER_HANDLER, CHAT_GROUP)

__mod_name__ = "USERS"
__handlers__ = [(USER_HANDLER, USERS_GROUP), BROADCAST_HANDLER, CHATLIST_HANDLER]
# <================================================ END =======================================================>
