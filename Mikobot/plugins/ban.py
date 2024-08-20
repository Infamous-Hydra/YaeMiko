import html

from telegram import (
    ChatMemberAdministrator,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, filters
from telegram.helpers import mention_html

from Mikobot import DEV_USERS, DRAGONS, LOGGER, OWNER_ID, function
from Mikobot.plugins.disable import DisableAbleCommandHandler
from Mikobot.plugins.helper_funcs.chat_status import (
    can_delete,
    check_admin,
    connection_status,
    is_user_admin,
    is_user_ban_protected,
    is_user_in_chat,
)
from Mikobot.plugins.helper_funcs.extraction import extract_user_and_text
from Mikobot.plugins.helper_funcs.misc import mention_username
from Mikobot.plugins.helper_funcs.string_handling import extract_time
from Mikobot.plugins.log_channel import gloggable, loggable

BAN_STICKER = "CAACAgUAAxkBAAEGWC5lloYv1tiI3-KPguoH5YX-RveWugACoQ4AAi4b2FQGdUhawbi91DQE"


@connection_status
@loggable
@check_admin(permission="can_restrict_members", is_both=True)
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot = context.bot
    args = context.args
    user_id, reason = await extract_user_and_text(message, context, args)

    member = await chat.get_member(user.id)
    SILENT = bool(True if message.text.startswith("/s") else False)

    # if update is coming from anonymous admin then send button and return.
    if message.from_user.id == 1087968824:
        if SILENT:
            await message.reply_text("Currently /sban won't work for anoymous admins.")
            return log_message
        # Need chat title to be forwarded on callback data to mention channel after banning.
        try:
            chat_title = message.reply_to_message.sender_chat.title
        except AttributeError:
            chat_title = None
        await update.effective_message.reply_text(
            text="You are an anonymous admin.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Click to prove Admin.",
                            callback_data=f"bans_{chat.id}=ban={user_id}={reason}={chat_title}",
                        ),
                    ],
                ]
            ),
        )

        return log_message
    elif (
        not (
            (
                member.can_restrict_members
                if isinstance(member, ChatMemberAdministrator)
                else None
            )
            or member.status == "creator"
        )
        and user.id not in DRAGONS
    ):
        await update.effective_message.reply_text(
            "Sorry son, but you're not worthy to wield the banhammer.",
        )
        return log_message

    if user_id == bot.id:
        await message.reply_text("Oh yeah, ban myself, noob!")
        return log_message

    if user_id is not None and user_id < 0:
        CHAT_SENDER = True
        chat_sender = message.reply_to_message.sender_chat
    else:
        CHAT_SENDER = False
        try:
            member = await chat.get_member(user_id)
        except BadRequest as excp:
            if excp.message == "User not found":
                raise
            elif excp == "Invalid user_id specified":
                await message.reply_text("I Doubt that's a user.")
            await message.reply_text("Can't find this person here.")
            return log_message

        if await is_user_ban_protected(chat, user_id, member) and user not in DEV_USERS:
            if user_id == OWNER_ID:
                await message.reply_text(
                    "Trying to put me against a God level disaster huh?"
                )
            elif user_id in DEV_USERS:
                await message.reply_text("I can't act against our own.")
            elif user_id in DRAGONS:
                await message.reply_text(
                    "Fighting this Dragon here will put me and my people's at risk.",
                )
            else:
                await message.reply_text("This user has immunity and cannot be banned.")
            return log_message

    if SILENT:
        silent = True
        if not await can_delete(chat, context.bot.id):
            return ""
    else:
        silent = False

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#{'S' if silent else ''}BANNED\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
    )

    reply = f"<code>❕</code><b>Ban Event</b>\n"

    if CHAT_SENDER:
        log += f"<b>Channel:</b> {mention_username(chat_sender.username, html.escape(chat_sender.title))}"
        reply += f"<code> </code><b>•  Channel:</b> {mention_username(chat_sender.username, html.escape(chat_sender.title))}"

    else:
        log += f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
        reply += f"<code> </code><b>•  User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"

    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        if CHAT_SENDER:
            await chat.ban_sender_chat(sender_chat_id=chat_sender.id)
        else:
            await chat.ban_member(user_id)

        if silent:
            if message.reply_to_message:
                await message.reply_to_message.delete()
            await message.delete()
            return log

        await bot.send_sticker(
            chat.id,
            BAN_STICKER,
            message_thread_id=message.message_thread_id if chat.is_forum else None,
        )  # banhammer marie sticker

        if reason:
            reply += f"\n<code> </code><b>•  Reason:</b> \n{html.escape(reason)}"
        await bot.sendMessage(
            chat.id,
            reply,
            parse_mode=ParseMode.HTML,
            message_thread_id=message.message_thread_id if chat.is_forum else None,
        )
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            if silent:
                return log
            await message.reply_text("Banned!", quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR banning user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            await message.reply_text("Uhm...that didn't work...")

    return log_message


@connection_status
@loggable
@check_admin(permission="can_restrict_members", is_both=True)
async def temp_ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = await extract_user_and_text(message, context, args)

    if not user_id:
        await message.reply_text("I doubt that's a user.")
        return log_message

    try:
        member = await chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise
        await message.reply_text("I can't seem to find this user.")
        return log_message
    if user_id == bot.id:
        await message.reply_text("I'm not gonna BAN myself, are you crazy?")
        return log_message

    if await is_user_ban_protected(chat, user_id, member):
        await message.reply_text("I don't feel like it.")
        return log_message

    if not reason:
        await message.reply_text("You haven't specified a time to ban this user for!")
        return log_message

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    reason = split_reason[1] if len(split_reason) > 1 else ""
    bantime = await extract_time(message, time_val)

    if not bantime:
        return log_message

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        "#TEMP BANNED\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}\n"
        f"<b>Time:</b> {time_val}"
    )
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        await chat.ban_member(user_id, until_date=bantime)
        await bot.send_sticker(
            chat.id,
            BAN_STICKER,
            message_thread_id=message.message_thread_id if chat.is_forum else None,
        )  # banhammer marie sticker
        await bot.sendMessage(
            chat.id,
            f"Banned! User {mention_html(member.user.id, html.escape(member.user.first_name))} "
            f"will be banned for {time_val}.",
            parse_mode=ParseMode.HTML,
            message_thread_id=message.message_thread_id if chat.is_forum else None,
        )
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            await message.reply_text(
                f"Banned! User will be banned for {time_val}.",
                quote=False,
            )
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR banning user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            await message.reply_text("Well damn, I can't ban that user.")

    return log_message


@connection_status
@loggable
@check_admin(permission="can_restrict_members", is_both=True)
async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = await extract_user_and_text(message, context, args)

    if not user_id:
        await message.reply_text("I doubt that's a user.")
        return log_message

    try:
        member = await chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise

        await message.reply_text("I can't seem to find this user.")
        return log_message
    if user_id == bot.id:
        await message.reply_text("Yeahhh I'm not gonna do that.")
        return log_message

    if await is_user_ban_protected(chat, user_id):
        await message.reply_text("I really wish I could kick this user....")
        return log_message

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        await bot.send_sticker(
            chat.id,
            BAN_STICKER,
            message_thread_id=message.message_thread_id if chat.is_forum else None,
        )  # banhammer marie sticker
        await bot.sendMessage(
            chat.id,
            f"Capitain I have kicked, {mention_html(member.user.id, html.escape(member.user.first_name))}.",
            parse_mode=ParseMode.HTML,
            message_thread_id=message.message_thread_id if chat.is_forum else None,
        )
        log = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#KICKED\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
        )
        if reason:
            log += f"\n<b>Reason:</b> {reason}"

        return log

    else:
        await message.reply_text("Well damn, I can't kick that user.")

    return log_message


@check_admin(permission="can_restrict_members", is_bot=True)
async def kickme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_message.from_user.id
    if await is_user_admin(update.effective_chat, user_id):
        await update.effective_message.reply_text(
            "I wish I could... but you're an admin."
        )
        return

    res = await update.effective_chat.unban_member(
        user_id
    )  # unban on current user = kick
    # BUG: parsing not working
    if res:
        await update.effective_message.reply_text(
            html.escape("You got the Devil's Kiss, Now die in peace"), parse_mode="html"
        )
    else:
        await update.effective_message.reply_text("Huh? I can't :/")


@connection_status
@loggable
@check_admin(permission="can_restrict_members", is_both=True)
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = await extract_user_and_text(message, context, args)

    if message.from_user.id == 1087968824:
        try:
            chat_title = message.reply_to_message.sender_chat.title
        except AttributeError:
            chat_title = None

        await message.reply_text(
            text="You are an anonymous admin.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Click to prove Admin.",
                            callback_data=f"bans_{chat.id}=unban={user_id}={reason}={chat_title}",
                        ),
                    ],
                ]
            ),
        )

        return log_message

    if not user_id:
        await message.reply_text("I doubt that's a user.")
        return log_message

    if user_id == bot.id:
        await message.reply_text("How would I unban myself if I wasn't here...?")
        return log_message

    if user_id is not None and user_id < 0:
        CHAT_SENDER = True
        chat_sender = message.reply_to_message.sender_chat
    else:
        CHAT_SENDER = False
        try:
            member = await chat.get_member(user_id)

            if isinstance(member, ChatMemberAdministrator):
                await message.reply_text(
                    "This person is an admin here, Are you drunk???"
                )
                return log_message

        except BadRequest as excp:
            raise
            if excp.message != "User not found":
                raise
            await message.reply_text("I can't seem to find this user.")
            return log_message

        if await is_user_in_chat(chat, user_id):
            await message.reply_text("Isn't this person already here??")
            return log_message

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNBANNED\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
    )

    if CHAT_SENDER:
        log += f"<b>User:</b> {mention_username(chat_sender.id, html.escape(chat_sender.title))}"
        await chat.unban_sender_chat(chat_sender.id)
        await message.reply_text("Yeah, this channel can speak again.")
    else:
        log += f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
        await chat.unban_member(user_id)
        await message.reply_text("Yeah, this user can join!")

    if reason:
        log += f"\n<b>Reason:</b> {reason}"

    return log


@connection_status
@gloggable
@check_admin(permission="can_restrict_members", is_bot=True)
async def selfunban(context: ContextTypes.DEFAULT_TYPE, update: Update) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    if user.id not in DRAGONS:
        return

    try:
        chat_id = int(args[0])
    except:
        await message.reply_text("Give a valid chat ID.")
        return

    chat = await bot.getChat(chat_id)

    try:
        member = await chat.get_member(user.id)
    except BadRequest as excp:
        if excp.message == "User not found":
            await message.reply_text("I can't seem to find this user.")
            return
        else:
            raise

    if await is_user_in_chat(chat, user.id):
        await message.reply_text("Aren't you already in the chat??")
        return

    await chat.unban_member(user.id)
    await message.reply_text("Yep, I have unbanned you.")

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNBANNED\n"
        f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
    )

    return log


@loggable
async def bans_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    bot = context.bot
    chat = update.effective_chat
    message = update.effective_message
    args = context.args
    log_message = ""
    splitter = query.data.replace("bans_", "").split("=")

    admin_user = query.from_user
    member = await chat.get_member(admin_user.id)

    if splitter[1] == "ban":
        # workaround for checking user admin status
        try:
            user_id = int(splitter[2])
        except ValueError:
            user_id = splitter[2]
        reason = splitter[3]
        chat_name = splitter[4]

        if not (
            (
                member.can_restrict_members
                if isinstance(member, ChatMemberAdministrator)
                else None
            )
            or member.status == "creator"
        ) and (admin_user.id not in DRAGONS):
            await query.answer(
                "Sorry son, but you're not worthy to wield the banhammer.",
                show_alert=True,
            )
            return log_message

        if user_id == bot.id:
            await message.edit_text("Oh yeah, ban myself, noob!")
            return log_message

        if isinstance(user_id, str):
            await message.edit_text("I doubt that's a user.")
            return log_message

        if user_id < 0:
            CHAT_SENDER = True
        else:
            CHAT_SENDER = False
            try:
                member = await chat.get_member(user_id)
            except BadRequest as excp:
                if excp.message == "User not found.":
                    raise
                elif excp == "Invalid user_id specified":
                    await message.edit_text("I Doubt that's a user.")
                await message.edit_text("Can't find this person here.")

                return log_message

            if (
                await is_user_ban_protected(chat, user_id, member)
                and admin_user not in DEV_USERS
            ):
                if user_id == OWNER_ID:
                    await message.edit_text(
                        "Trying to put me against a God level disaster huh?"
                    )
                elif user_id in DEV_USERS:
                    await message.edit_text("I can't act against our own.")
                elif user_id in DRAGONS:
                    await message.edit_text(
                        "Fighting this Dragon here will put me and my people's at risk.",
                    )
                else:
                    await message.edit_text(
                        "This user has immunity and cannot be banned."
                    )
                return log_message

        log = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#BANNED\n"
            f"<b>Admin:</b> {mention_html(admin_user.id, html.escape(admin_user.first_name))}\n"
        )

        reply = f"<code>❕</code><b>Ban Event</b>\n"

        if CHAT_SENDER:
            log += f"<b>Channel:</b> {html.escape(chat_name)}"
            reply += f"<code> </code><b>•  Channel:</b> {html.escape(chat_name)}"

        else:
            log += f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
            reply += f"<code> </code><b>•  User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"

        if reason:
            log += "\n<b>Reason:</b> {}".format(reason)

        try:
            if CHAT_SENDER:
                await chat.ban_sender_chat(sender_chat_id=user_id)
            else:
                await chat.ban_member(user_id)

            await bot.send_sticker(
                chat.id,
                BAN_STICKER,
                message_thread_id=message.message_thread_id if chat.is_forum else None,
            )  # banhammer marie sticker

            if reason:
                reply += f"\n<code> </code><b>•  Reason:</b> \n{html.escape(reason)}"
            await bot.sendMessage(
                chat.id,
                reply,
                parse_mode=ParseMode.HTML,
                message_thread_id=message.message_thread_id if chat.is_forum else None,
            )
            await query.answer(f"Done Banned User.")
            return log

        except BadRequest as excp:
            if excp.message == "Reply message not found":
                # Do not reply
                await message.edit_text("Banned!")
                return log
            else:
                LOGGER.warning(update)
                LOGGER.exception(
                    "ERROR banning user %s in chat %s (%s) due to %s",
                    user_id,
                    chat.title,
                    chat.id,
                    excp.message,
                )
                await message.edit_text("Uhm...that didn't work...")

        return log_message

    elif splitter[1] == "unban":
        try:
            user_id = int(splitter[2])
        except ValueError:
            user_id = splitter[2]
        reason = splitter[3]

        if isinstance(user_id, str):
            await message.edit_text("I doubt that's a user.")
            return log_message

        if user_id == bot.id:
            await message.edit_text("How would i unban myself if i wasn't here...?")
            return log_message

        if user_id < 0:
            CHAT_SENDER = True
            chat_title = splitter[4]
        else:
            CHAT_SENDER = False

            try:
                member = await chat.get_member(user_id)
            except BadRequest as excp:
                if excp.message != "User not found":
                    raise
                await message.edit_text("I can't seem to find this user.")
                return log_message

            if await is_user_in_chat(chat, user_id):
                await message.edit_text("Isn't this person already here??")
                return log_message

        log = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#UNBANNED\n"
            f"<b>Admin:</b> {mention_html(admin_user.id, html.escape(admin_user.first_name))}\n"
        )

        if CHAT_SENDER:
            log += f"<b>User:</b> {html.escape(chat_title)}"
            await chat.unban_sender_chat(user_id)
            await message.reply_text("Yeah, this channel can speak again.")
        else:
            log += f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
            await chat.unban_member(user_id)
            await message.reply_text("Yeah, this user can join!")

        if reason:
            log += f"\n<b>Reason:</b> {reason}"

        return log


__help__ = """
» /kickme: kicks the user who issued the command

➠ *Admins only:*
» /ban <userhandle>: bans a user/channel. (via handle, or reply)

» /sban <userhandle>: Silently ban a user. Deletes command, Replied message and doesn't reply. (via handle, or reply)

» /tban <userhandle> x(m/h/d): bans a user for `x` time. (via handle, or reply). `m` = `minutes`, `h` = `hours`, `d` = `days`.

» /unban <userhandle>: unbans a user/channel. (via handle, or reply)

» /kick <userhandle>: kicks a user out of the group, (via handle, or reply)

➠ NOTE:
    Banning or UnBanning channels only work if you reply to their message, so don't use their username to ban/unban.
"""

BAN_HANDLER = CommandHandler(["ban", "sban"], ban, block=False)
TEMPBAN_HANDLER = CommandHandler(["tban"], temp_ban, block=False)
KICK_HANDLER = CommandHandler("kick", kick, block=False)
UNBAN_HANDLER = CommandHandler("unban", unban, block=False)
ROAR_HANDLER = CommandHandler("roar", selfunban, block=False)
KICKME_HANDLER = DisableAbleCommandHandler(
    "kickme", kickme, filters=filters.ChatType.GROUPS, block=False
)
BAN_CALLBACK_HANDLER = CallbackQueryHandler(
    bans_callback, block=False, pattern=r"bans_"
)

function(BAN_HANDLER)
function(TEMPBAN_HANDLER)
function(KICK_HANDLER)
function(UNBAN_HANDLER)
function(ROAR_HANDLER)
function(KICKME_HANDLER)
function(BAN_CALLBACK_HANDLER)

__mod_name__ = "BAN"
__handlers__ = [
    BAN_HANDLER,
    TEMPBAN_HANDLER,
    KICK_HANDLER,
    UNBAN_HANDLER,
    ROAR_HANDLER,
    KICKME_HANDLER,
    BAN_CALLBACK_HANDLER,
]
