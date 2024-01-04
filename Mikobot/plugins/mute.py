# <============================================== IMPORTS =========================================================>
import html
from typing import Union

from telegram import Bot, Chat, ChatMember, ChatPermissions, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, ContextTypes
from telegram.helpers import mention_html

from Mikobot import LOGGER, function
from Mikobot.plugins.helper_funcs.chat_status import (
    check_admin,
    connection_status,
    is_user_admin,
)
from Mikobot.plugins.helper_funcs.extraction import extract_user, extract_user_and_text
from Mikobot.plugins.helper_funcs.string_handling import extract_time
from Mikobot.plugins.log_channel import loggable

# <=======================================================================================================>


# <================================================ FUNCTION =======================================================>
async def check_user(user_id: int, bot: Bot, chat: Chat) -> Union[str, None]:
    if not user_id:
        reply = "You don't seem to be referring to a user or the ID specified is incorrect.."
        return reply

    try:
        member = await chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            reply = "I can't seem to find this user"
            return reply
        else:
            raise

    if user_id == bot.id:
        reply = "I'm not gonna MUTE myself, How high are you?"
        return reply

    if await is_user_admin(chat, user_id, member):
        reply = "Sorry can't do that, this user is admin here."
        return reply

    return None


@connection_status
@loggable
@check_admin(permission="can_restrict_members", is_both=True)
async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id, reason = await extract_user_and_text(message, context, args)
    reply = await check_user(user_id, bot, chat)

    if reply:
        await message.reply_text(reply)
        return ""

    member = await chat.get_member(user_id)

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#MUTE\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
    )

    if reason:
        log += f"\n<b>Reason:</b> {reason}"

    if member.status in [ChatMember.RESTRICTED, ChatMember.MEMBER]:
        chat_permissions = ChatPermissions(can_send_messages=False)
        await bot.restrict_chat_member(chat.id, user_id, chat_permissions)
        await bot.sendMessage(
            chat.id,
            f"Muted <b>{html.escape(member.user.first_name)}</b> with no expiration date!",
            parse_mode=ParseMode.HTML,
            message_thread_id=message.message_thread_id if chat.is_forum else None,
        )
        return log

    else:
        await message.reply_text("This user is already muted!")

    return ""


@connection_status
@loggable
@check_admin(permission="can_restrict_members", is_both=True)
async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id = await extract_user(message, context, args)
    if not user_id:
        await message.reply_text(
            "You'll need to either give me a username to unmute, or reply to someone to be unmuted.",
        )
        return ""

    member = await chat.get_member(int(user_id))

    if member.status not in [ChatMember.LEFT, ChatMember.BANNED]:
        if member.status != ChatMember.RESTRICTED:
            await message.reply_text("This user already has the right to speak.")
        else:
            chat_permissions = ChatPermissions(
                can_send_messages=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_send_polls=True,
                can_change_info=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            )
            try:
                await bot.restrict_chat_member(chat.id, int(user_id), chat_permissions)
            except BadRequest:
                pass
            await bot.sendMessage(
                chat.id,
                f"I shall allow <b>{html.escape(member.user.first_name)}</b> to text!",
                parse_mode=ParseMode.HTML,
                message_thread_id=message.message_thread_id if chat.is_forum else None,
            )
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#UNMUTE\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
            )
    else:
        await message.reply_text(
            "This user isn't even in the chat, unmuting them won't make them talk more than they "
            "already do!",
        )

    return ""


@connection_status
@loggable
@check_admin(permission="can_restrict_members", is_both=True)
async def temp_mute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id, reason = await extract_user_and_text(message, context, args)
    reply = await check_user(user_id, bot, chat)

    if reply:
        await message.reply_text(reply)
        return ""

    member = await chat.get_member(user_id)

    if not reason:
        await message.reply_text("You haven't specified a time to mute this user for!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    mutetime = await extract_time(message, time_val)

    if not mutetime:
        return ""

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#TEMP MUTED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}\n"
        f"<b>Time:</b> {time_val}"
    )
    if reason:
        log += f"\n<b>Reason:</b> {reason}"

    try:
        if member.status in [ChatMember.RESTRICTED, ChatMember.MEMBER]:
            chat_permissions = ChatPermissions(can_send_messages=False)
            await bot.restrict_chat_member(
                chat.id,
                user_id,
                chat_permissions,
                until_date=mutetime,
            )
            await bot.sendMessage(
                chat.id,
                f"Muted <b>{html.escape(member.user.first_name)}</b> for {time_val}!",
                parse_mode=ParseMode.HTML,
                message_thread_id=message.message_thread_id if chat.is_forum else None,
            )
            return log
        else:
            await message.reply_text("This user is already muted.")

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            await message.reply_text(f"Muted for {time_val}!", quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR muting user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            await message.reply_text("Well damn, I can't mute that user.")

    return ""


# <=================================================== HELP ====================================================>


__help__ = """
➠ *Admins only:*

» /mute <userhandle>: silences a user. Can also be used as a reply, muting the replied to user.

» /tmute <userhandle> x(m/h/d): mutes a user for x time. (via handle, or reply). `m` = `minutes`, `h` = `hours`, `d` = `days`.

» /unmute <userhandle>: unmutes a user. Can also be used as a reply, muting the replied to user.
"""

# <================================================ HANDLER =======================================================>
MUTE_HANDLER = CommandHandler("mute", mute, block=False)
UNMUTE_HANDLER = CommandHandler("unmute", unmute, block=False)
TEMPMUTE_HANDLER = CommandHandler(["tmute", "tempmute"], temp_mute, block=False)

function(MUTE_HANDLER)
function(UNMUTE_HANDLER)
function(TEMPMUTE_HANDLER)

__mod_name__ = "MUTE"
__handlers__ = [MUTE_HANDLER, UNMUTE_HANDLER, TEMPMUTE_HANDLER]
# <================================================ END =======================================================>
