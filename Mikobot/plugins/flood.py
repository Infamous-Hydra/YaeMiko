# <============================================== IMPORTS =========================================================>
import html
import re

from telegram import ChatPermissions, Update
from telegram.error import BadRequest
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.helpers import mention_html

from Database.sql import antiflood_sql as sql
from Database.sql.approve_sql import is_approved
from Mikobot import dispatcher, function
from Mikobot.plugins.connection import connected
from Mikobot.plugins.helper_funcs.alternate import send_message
from Mikobot.plugins.helper_funcs.chat_status import check_admin, is_user_admin
from Mikobot.plugins.helper_funcs.string_handling import extract_time
from Mikobot.plugins.log_channel import loggable

# <=======================================================================================================>

FLOOD_GROUP = 3


# <================================================ FUNCTION =======================================================>
@loggable
async def check_flood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message
    if not user:
        return ""

    if await is_user_admin(chat, user.id):
        sql.update_flood(chat.id, None)
        return ""

    if is_approved(chat.id, user.id):
        sql.update_flood(chat.id, None)
        return

    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return ""

    try:
        getmode, getvalue = sql.get_flood_setting(chat.id)
        if getmode == 1:
            await chat.ban_member(user.id)
            execstrings = "BANNED"
            tag = "BANNED"
        elif getmode == 2:
            await chat.ban_member(user.id)
            await chat.unban_member(user.id)
            execstrings = "KICKED"
            tag = "KICKED"
        elif getmode == 3:
            await context.bot.restrict_chat_member(
                chat.id,
                user.id,
                permissions=ChatPermissions(can_send_messages=False),
            )
            execstrings = "MUTED"
            tag = "MUTED"
        elif getmode == 4:
            bantime = await extract_time(msg, getvalue)
            await chat.ban_member(user.id, until_date=bantime)
            execstrings = "BANNED for {}".format(getvalue)
            tag = "TBAN"
        elif getmode == 5:
            mutetime = await extract_time(msg, getvalue)
            await context.bot.restrict_chat_member(
                chat.id,
                user.id,
                until_date=mutetime,
                permissions=ChatPermissions(can_send_messages=False),
            )
            execstrings = "MUTED for {}".format(getvalue)
            tag = "TMUTE"
        await send_message(
            update.effective_message,
            "Beep boop! Boop beep!\n{}!".format(execstrings),
        )

        return (
            "<b>{}:</b>"
            "\n#{}"
            "\n<b>user:</b> {}"
            "\nFlooded the group.".format(
                tag,
                html.escape(chat.title),
                mention_html(user.id, html.escape(user.first_name)),
            )
        )

    except BadRequest:
        await msg.reply_text(
            "I can't restrict people here, give me permissions first! Until then, I'll disable anti-flood.",
        )
        sql.set_flood(chat.id, 0)
        return (
            "<b>{}:</b>"
            "\n#INFO"
            "\nDon't have enough permission to restrict users so automatically disabled anti-flood.".format(
                chat.title,
            )
        )


@check_admin(permission="can_restrict_members", is_both=True, no_reply=True)
async def flood_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    query = update.callback_query
    user = update.effective_user
    match = re.match(r"unmute_flooder\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat = update.effective_chat.id
        try:
            await bot.restrict_chat_member(
                chat,
                int(user_id),
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                ),
            )
            await update.effective_message.edit_text(
                f"Unmuted by {mention_html(user.id, html.escape(user.first_name))}.",
                parse_mode="HTML",
            )
        except:
            pass


@loggable
@check_admin(is_user=True)
async def set_flood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    args = context.args

    conn = await connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat_id = conn
        chat_obj = await dispatcher.bot.getChat(conn)
        chat_name = chat_obj.title
    else:
        if update.effective_message.chat.type == "private":
            await send_message(
                update.effective_message,
                "This command is meant to use in a group, not in PM.",
            )
            return ""
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if len(args) >= 1:
        val = args[0].lower()
        if val in ["off", "no", "0"]:
            sql.set_flood(chat_id, 0)
            if conn:
                text = await message.reply_text(
                    "Antiflood has been disabled in {}.".format(chat_name),
                )
            else:
                text = await message.reply_text("Antiflood has been disabled.")

        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                sql.set_flood(chat_id, 0)
                if conn:
                    text = await message.reply_text(
                        "Antiflood has been disabled in {}.".format(chat_name),
                    )
                else:
                    text = await message.reply_text("Antiflood has been disabled.")
                return (
                    "<b>{}:</b>"
                    "\n#SETFLOOD"
                    "\n<b>Admin:</b> {}"
                    "\nDisable Antiflood.".format(
                        html.escape(chat_name),
                        mention_html(user.id, html.escape(user.first_name)),
                    )
                )

            elif amount <= 3:
                await send_message(
                    update.effective_message,
                    "Antiflood must be either 0 (disabled) or a number greater than 3!",
                )
                return ""

            else:
                sql.set_flood(chat_id, amount)
                if conn:
                    text = await message.reply_text(
                        "Antiflood limit has been set to {} in chat: {}".format(
                            amount,
                            chat_name,
                        ),
                    )
                else:
                    text = await message.reply_text(
                        "Successfully updated antiflood limit to {}!".format(amount),
                    )
                return (
                    "<b>{}:</b>"
                    "\n#SETFLOOD"
                    "\n<b>Admin:</b> {}"
                    "\nSet Antiflood to <code>{}</code>.".format(
                        html.escape(chat_name),
                        mention_html(user.id, html.escape(user.first_name)),
                        amount,
                    )
                )

        else:
            await message.reply_text(
                "Invalid argument, please use a number, 'off', or 'no'."
            )
    else:
        await message.reply_text(
            (
                "Use `/setflood number` to enable antiflood.\n"
                "Or use `/setflood off` to disable antiflood."
            ),
            parse_mode="markdown",
        )
    return ""


async def flood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    conn = await connected(context.bot, update, chat, user.id, need_admin=False)
    if conn:
        chat_id = conn
        chat_obj = await dispatcher.bot.getChat(conn)
        chat_name = chat_obj.title
    else:
        if update.effective_message.chat.type == "private":
            await send_message(
                update.effective_message,
                "This command is meant to use in a group, not in PM.",
            )
            return
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        if conn:
            text = await msg.reply_text(
                "I'm not enforcing any flood control in {}!".format(chat_name),
            )
        else:
            text = await msg.reply_text("I'm not enforcing any flood control here!")
    else:
        if conn:
            text = await msg.reply_text(
                "I'm currently restricting members after {} consecutive messages in {}.".format(
                    limit,
                    chat_name,
                ),
            )
        else:
            text = await msg.reply_text(
                "I'm currently restricting members after {} consecutive messages.".format(
                    limit,
                ),
            )


@check_admin(is_user=True)
async def set_flood_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    args = context.args

    conn = await connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = await dispatcher.bot.getChat(conn)
        chat_id = conn
        chat_obj = await dispatcher.bot.getChat(conn)
        chat_name = chat_obj.title
    else:
        if update.effective_message.chat.type == "private":
            await send_message(
                update.effective_message,
                "This command is meant to use in a group, not in PM.",
            )
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if args:
        if args[0].lower() == "ban":
            settypeflood = "ban"
            sql.set_flood_strength(chat_id, 1, "0")
        elif args[0].lower() == "kick":
            settypeflood = "kick"
            sql.set_flood_strength(chat_id, 2, "0")
        elif args[0].lower() == "mute":
            settypeflood = "mute"
            sql.set_flood_strength(chat_id, 3, "0")
        elif args[0].lower() == "tban":
            if len(args) == 1:
                teks = """It looks like you tried to set time value for antiflood but you didn't specified time; Try, `/setfloodmode tban <timevalue>`.
Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                await send_message(
                    update.effective_message, teks, parse_mode="markdown"
                )
                return
            settypeflood = "tban for {}".format(args[1])
            sql.set_flood_strength(chat_id, 4, str(args[1]))
        elif args[0].lower() == "tmute":
            if len(args) == 1:
                teks = """It looks like you tried to set time value for antiflood but you didn't specified time; Try, `/setfloodmode tmute <timevalue>`.
Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                await send_message(
                    update.effective_message, teks, parse_mode="markdown"
                )
                return
            settypeflood = "tmute for {}".format(args[1])
            sql.set_flood_strength(chat_id, 5, str(args[1]))
        else:
            await send_message(
                update.effective_message,
                "I only understand ban/kick/mute/tban/tmute!",
            )
            return
        if conn:
            text = await msg.reply_text(
                "Exceeding consecutive flood limit will result in {} in {}!".format(
                    settypeflood,
                    chat_name,
                ),
            )
        else:
            text = await msg.reply_text(
                "Exceeding consecutive flood limit will result in {}!".format(
                    settypeflood,
                ),
            )
        return (
            "<b>{}:</b>\n"
            "<b>Admin:</b> {}\n"
            "Has changed antiflood mode. User will {}.".format(
                settypeflood,
                html.escape(chat.title),
                mention_html(user.id, html.escape(user.first_name)),
            )
        )
    else:
        getmode, getvalue = sql.get_flood_setting(chat.id)
        if getmode == 1:
            settypeflood = "ban"
        elif getmode == 2:
            settypeflood = "kick"
        elif getmode == 3:
            settypeflood = "mute"
        elif getmode == 4:
            settypeflood = "tban for {}".format(getvalue)
        elif getmode == 5:
            settypeflood = "tmute for {}".format(getvalue)
        if conn:
            text = await msg.reply_text(
                "Sending more messages than flood limit will result in {} in {}.".format(
                    settypeflood,
                    chat_name,
                ),
            )
        else:
            text = await msg.reply_text(
                "Sending more messages than flood limit will result in {}.".format(
                    settypeflood,
                ),
            )
    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        return "Not enforcing flood control."
    else:
        return "Antiflood has been set to `{}`.".format(limit)


# <=================================================== HELP ====================================================>


__help__ = """
➠ *Antiflood allows you to take action on users that send more than x messages in a row. Exceeding the set flood will result in restricting that user.*

➠ *Admin Only*

» /flood: Get the current antiflood settings.

» /setflood <number/off/no>: Set the number of messages after which to take action on a user. Set to '0', 'off', or 'no' to disable.

» /setfloodmode <action type>: Choose which action to take on a user who has been flooding. Options: ban/kick/mute/tban/tmute.
"""

__mod_name__ = "ANTI-FLOOD"

# <================================================ HANDLER =======================================================>
FLOOD_BAN_HANDLER = MessageHandler(
    filters.ALL & ~filters.StatusUpdate.ALL & filters.ChatType.GROUPS,
    check_flood,
    block=False,
)
SET_FLOOD_HANDLER = CommandHandler(
    "setflood", set_flood, filters=filters.ChatType.GROUPS, block=False
)
SET_FLOOD_MODE_HANDLER = CommandHandler(
    "setfloodmode", set_flood_mode, block=False
)  # , filters=filters.ChatType.GROUPS)
FLOOD_QUERY_HANDLER = CallbackQueryHandler(
    flood_button, pattern=r"unmute_flooder", block=False
)
FLOOD_HANDLER = CommandHandler(
    "flood", flood, filters=filters.ChatType.GROUPS, block=False
)

function(FLOOD_BAN_HANDLER, FLOOD_GROUP)
function(FLOOD_QUERY_HANDLER)
function(SET_FLOOD_HANDLER)
function(SET_FLOOD_MODE_HANDLER)
function(FLOOD_HANDLER)

__handlers__ = [
    (FLOOD_BAN_HANDLER, FLOOD_GROUP),
    SET_FLOOD_HANDLER,
    FLOOD_HANDLER,
    SET_FLOOD_MODE_HANDLER,
]
# <================================================ END =======================================================>
