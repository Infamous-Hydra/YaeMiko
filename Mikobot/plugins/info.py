# <============================================== IMPORTS =========================================================>
import asyncio
import os
import re
from html import escape
from random import choice

from telegram import (
    ChatMemberAdministrator,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ChatID, ChatType, ParseMode
from telegram.error import BadRequest, Forbidden
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes
from telegram.helpers import mention_html

import Database.sql.global_bans_sql as gban_sql
import Database.sql.users_sql as user_sql
from Database.sql.approve_sql import is_approved
from Infamous.karma import START_IMG
from Mikobot import DEV_USERS, DRAGONS, INFOPIC, OWNER_ID, function
from Mikobot.__main__ import STATS, USER_INFO
from Mikobot.plugins.helper_funcs.chat_status import check_admin, support_plus
from Mikobot.plugins.users import get_user_id

# <=======================================================================================================>


# <================================================ FUNCTION =======================================================>
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args
    bot = context.bot

    def reply_with_text(text):
        return message.reply_text(text, parse_mode=ParseMode.HTML)

    head = ""
    premium = False

    reply = await reply_with_text("<code>Getting information...</code>")

    user_id = None
    user_name = None

    if len(args) >= 1:
        if args[0][0] == "@":
            user_name = args[0]
            user_id = await get_user_id(user_name)

        if not user_id:
            try:
                chat_obj = await bot.get_chat(user_name)
                userid = chat_obj.id
            except BadRequest:
                await reply_with_text(
                    "I can't get information about this user/channel/group."
                )
                return
        else:
            userid = user_id
    elif len(args) >= 1 and args[0].lstrip("-").isdigit():
        userid = int(args[0])
    elif message.reply_to_message and not message.reply_to_message.forum_topic_created:
        if message.reply_to_message.sender_chat:
            userid = message.reply_to_message.sender_chat.id
        elif message.reply_to_message.from_user:
            if message.reply_to_message.from_user.id == ChatID.FAKE_CHANNEL:
                userid = message.reply_to_message.chat.id
            else:
                userid = message.reply_to_message.from_user.id
                premium = message.reply_to_message.from_user.is_premium
    elif not message.reply_to_message and not args:
        if message.from_user.id == ChatID.FAKE_CHANNEL:
            userid = message.sender_chat.id
        else:
            userid = message.from_user.id
            premium = message.from_user.is_premium

    try:
        chat_obj = await bot.get_chat(userid)
    except (BadRequest, UnboundLocalError):
        await reply_with_text("I can't get information about this user/channel/group.")
        return

    if chat_obj.type == ChatType.PRIVATE:
        if chat_obj.username:
            head = f"⇨【 <b>USER INFORMATION</b> 】⇦\n\n"
            if chat_obj.username.endswith("bot"):
                head = f"⇨【 <b>BOT INFORMATION</b> 】⇦\n\n"

        head += f"➲ <b>ID:</b> <code>{chat_obj.id}</code>"
        head += f"\n➲ <b>First Name:</b> {chat_obj.first_name}"
        if chat_obj.last_name:
            head += f"\n➲ <b>Last Name:</b> {chat_obj.last_name}"
        if chat_obj.username:
            head += f"\n➲ <b>Username:</b> @{chat_obj.username}"
        head += f"\n➲ <b>Permalink:</b> {mention_html(chat_obj.id, 'link')}"

        if chat_obj.username and not chat_obj.username.endswith("bot"):
            head += f"\n\n💎 <b>Premium User:</b> {premium}"

        if chat_obj.bio:
            head += f"\n\n<b>➲ Bio:</b> {chat_obj.bio}"

        chat_member = await chat.get_member(chat_obj.id)
        if isinstance(chat_member, ChatMemberAdministrator):
            head += f"\n➲ <b>Presence:</b> {chat_member.status}"
            if chat_member.custom_title:
                head += f"\n➲ <b>Admin Title:</b> {chat_member.custom_title}"
        else:
            head += f"\n➲ <b>Presence:</b> {chat_member.status}"

        if is_approved(chat.id, chat_obj.id):
            head += f"\n➲ <b>Approved:</b> This user is approved in this chat."

        disaster_level_present = False

        if chat_obj.id == OWNER_ID:
            head += "\n\n👑 <b>The disaster level of this person is My Owner.</b>"
            disaster_level_present = True
        elif chat_obj.id in DEV_USERS:
            head += "\n\n🐉 <b>This user is a member of Infamous Hydra.</b>"
            disaster_level_present = True
        elif chat_obj.id in DRAGONS:
            head += "\n\n🐲 <b>The disaster level of this person is Dragon.</b>"
            disaster_level_present = True
        if disaster_level_present:
            head += " [?]"

        for mod in USER_INFO:
            try:
                mod_info = mod.__user_info__(chat_obj.id).strip()
            except TypeError:
                mod_info = mod.__user_info__(chat_obj.id, chat.id).strip()

            head += "\n\n" + mod_info if mod_info else ""

    if chat_obj.type == ChatType.SENDER:
        head = f"📨 Sender Chat Information:\n"
        await reply_with_text("Found sender chat, getting information...")
        head += f"<b>ID:</b> <code>{chat_obj.id}</code>"
        if chat_obj.title:
            head += f"\n🏷️ <b>Title:</b> {chat_obj.title}"
        if chat_obj.username:
            head += f"\n📧 <b>Username:</b> @{chat_obj.username}"
        head += f"\n🔗 Permalink: {mention_html(chat_obj.id, 'link')}"
        if chat_obj.description:
            head += f"\n📝 <b>Description:</b> {chat_obj.description}"

    elif chat_obj.type == ChatType.CHANNEL:
        head = f"Channel Information:\n"
        await reply_with_text("Found channel, getting information...")
        head += f"<b>ID:</b> <code>{chat_obj.id}</code>"
        if chat_obj.title:
            head += f"\n<b>Title:</b> {chat_obj.title}"
        if chat_obj.username:
            head += f"\n<b>Username:</b> @{chat_obj.username}"
        head += f"\nPermalink: {mention_html(chat_obj.id, 'link')}"
        if chat_obj.description:
            head += f"\n<b>Description:</b> {chat_obj.description}"
        if chat_obj.linked_chat_id:
            head += f"\n<b>Linked Chat ID:</b> <code>{chat_obj.linked_chat_id}</code>"

    elif chat_obj.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        head = f"Group Information:\n"
        await reply_with_text("Found group, getting information...")
        head += f"<b>ID:</b> <code>{chat_obj.id}</code>"
        if chat_obj.title:
            head += f"\n<b>Title:</b> {chat_obj.title}"
        if chat_obj.username:
            head += f"\n<b>Username:</b> @{chat_obj.username}"
        head += f"\nPermalink: {mention_html(chat_obj.id, 'link')}"
        if chat_obj.description:
            head += f"\n<b>Description:</b> {chat_obj.description}"

    if INFOPIC:
        try:
            if chat_obj.photo:
                _file = await chat_obj.photo.get_big_file()
                await _file.download_to_drive(f"{chat_obj.id}.png")
                await message.reply_photo(
                    photo=open(f"{chat_obj.id}.png", "rb"),
                    caption=(head),
                    parse_mode=ParseMode.HTML,
                )
                await reply.delete()
                os.remove(f"{chat_obj.id}.png")
            else:
                await reply_with_text(escape(head))
        except:
            await reply_with_text(escape(head))


@support_plus
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = "📊 <b>Miko-Bot's Statistics:</b>\n\n" + "\n".join(
        [mod.__stats__() for mod in STATS]
    )
    result = re.sub(r"(\d+)", r"<code>\1</code>", stats)

    await update.effective_message.reply_photo(
        photo=str(choice(START_IMG)), caption=result, parse_mode=ParseMode.HTML
    )


async def get_invalid_chats(
    update: Update, context: ContextTypes.DEFAULT_TYPE, remove: bool = False
):
    bot = context.bot
    chat_id = update.effective_chat.id
    chats = user_sql.get_all_chats()
    kicked_chats, progress = 0, 0
    chat_list = []
    progress_message = None

    for chat in chats:
        if ((100 * chats.index(chat)) / len(chats)) > progress:
            progress_bar = f"{progress}% completed in getting invalid chats."
            if progress_message:
                try:
                    await bot.editMessageText(
                        progress_bar,
                        chat_id,
                        progress_message.message_id,
                    )
                except:
                    pass
            else:
                progress_message = await bot.sendMessage(
                    chat_id,
                    progress_bar,
                    message_thread_id=update.effective_message.message_thread_id
                    if update.effective_chat.is_forum
                    else None,
                )
            progress += 5

        cid = chat.chat_id
        await asyncio.sleep(0.1)
        try:
            await bot.get_chat(cid, timeout=60)
        except (BadRequest, Forbidden):
            kicked_chats += 1
            chat_list.append(cid)
        except:
            pass

    try:
        await progress_message.delete()
    except:
        pass

    if not remove:
        return kicked_chats
    else:
        for muted_chat in chat_list:
            await asyncio.sleep(0.1)
            user_sql.rem_chat(muted_chat)
        return kicked_chats


async def get_invalid_gban(
    update: Update, context: ContextTypes.DEFAULT_TYPE, remove: bool = False
):
    bot = context.bot
    banned = gban_sql.get_gban_list()
    ungbanned_users = 0
    ungban_list = []

    for user in banned:
        user_id = user["user_id"]
        await asyncio.sleep(0.1)
        try:
            await bot.get_chat(user_id)
        except BadRequest:
            ungbanned_users += 1
            ungban_list.append(user_id)
        except:
            pass

    if not remove:
        return ungbanned_users
    else:
        for user_id in ungban_list:
            await asyncio.sleep(0.1)
            gban_sql.ungban_user(user_id)
        return ungbanned_users


@check_admin(only_dev=True)
async def dbcleanup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    await msg.reply_text("Getting invalid chat count...")
    invalid_chat_count = await get_invalid_chats(update, context)

    await msg.reply_text("Getting invalid gban count...")
    invalid_gban_count = await get_invalid_gban(update, context)

    reply = f"Total invalid chats - {invalid_chat_count}\n"
    reply += f"Total invalid gban users - {invalid_gban_count}"

    buttons = [[InlineKeyboardButton("Cleanup DB", callback_data="db_cleanup")]]

    await update.effective_message.reply_text(
        reply,
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def callback_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    query = update.callback_query
    message = query.message
    chat_id = update.effective_chat.id
    query_type = query.data

    admin_list = [OWNER_ID] + DEV_USERS

    await bot.answer_callback_query(query.id)

    if query_type == "db_leave_chat":
        if query.from_user.id in admin_list:
            await bot.editMessageText("Leaving chats...", chat_id, message.message_id)
            chat_count = await get_invalid_chats(update, context, True)
            await bot.sendMessage(
                chat_id,
                f"Left {chat_count} chats.",
                message_thread_id=message.message_thread_id
                if update.effective_chat.is_forum
                else None,
            )
        else:
            await query.answer("You are not allowed to use this.")
    elif query_type == "db_cleanup":
        if query.from_user.id in admin_list:
            await bot.editMessageText("Cleaning up DB...", chat_id, message.message_id)
            invalid_chat_count = await get_invalid_chats(update, context, True)
            invalid_gban_count = await get_invalid_gban(update, context, True)
            reply = "Cleaned up {} chats and {} gban users from DB.".format(
                invalid_chat_count,
                invalid_gban_count,
            )
            await bot.sendMessage(
                chat_id,
                reply,
                message_thread_id=message.message_thread_id
                if update.effective_chat.is_forum
                else None,
            )
        else:
            await query.answer("You are not allowed to use this.")


# <=================================================== HELP ====================================================>


__help__ = """
*Overall information about user:*

» /info : Fetch information.
"""

# <================================================ HANDLER =======================================================>
STATS_HANDLER = CommandHandler(["stats", "gstats"], stats, block=False)
INFO_HANDLER = CommandHandler(("info", "book"), info, block=False)
DB_CLEANUP_HANDLER = CommandHandler("dbcleanup", dbcleanup, block=False)
BUTTON_HANDLER = CallbackQueryHandler(callback_button, pattern="db_.*", block=False)

function(DB_CLEANUP_HANDLER)
function(BUTTON_HANDLER)
function(STATS_HANDLER)
function(INFO_HANDLER)

__mod_name__ = "INFO"
__command_list__ = ["info"]
__handlers__ = [INFO_HANDLER, STATS_HANDLER, DB_CLEANUP_HANDLER, BUTTON_HANDLER]
# <================================================ END =======================================================>
