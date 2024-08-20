# <============================================== IMPORTS =========================================================>
from datetime import datetime
from functools import wraps

from telegram.constants import ChatType
from telegram.ext import ContextTypes

from Mikobot import function
from Mikobot.plugins.helper_funcs.misc import is_module_loaded

FILENAME = __name__.rsplit(".", 1)[-1]

if is_module_loaded(FILENAME):
    from telegram import Update
    from telegram.constants import ParseMode
    from telegram.error import BadRequest, Forbidden
    from telegram.ext import CommandHandler, JobQueue
    from telegram.helpers import escape_markdown

    from Database.sql import log_channel_sql as sql
    from Mikobot import EVENT_LOGS, LOGGER, dispatcher
    from Mikobot.plugins.helper_funcs.chat_status import check_admin

    # <=======================================================================================================>
    # <================================================ FUNCTION =======================================================>
    def loggable(func):
        @wraps(func)
        async def log_action(
            update: Update,
            context: ContextTypes.DEFAULT_TYPE,
            job_queue: JobQueue = None,
            *args,
            **kwargs,
        ):
            if not job_queue:
                result = await func(update, context, *args, **kwargs)
            else:
                result = await func(update, context, job_queue, *args, **kwargs)

            chat = update.effective_chat
            message = update.effective_message

            if result and isinstance(result, str):
                datetime_fmt = "%H:%M - %d-%m-%Y"
                result += f"\nEvent stamp: {datetime.utcnow().strftime(datetime_fmt)}"

                if chat.is_forum and chat.username:
                    result += f"\nLink: https://t.me/{chat.username}/{message.message_thread_id}/{message.message_id}"

                if message.chat.type == chat.SUPERGROUP and message.chat.username:
                    result += (
                        f"\nLink: https://t.me/{chat.username}/{message.message_id}"
                    )
                log_chat = sql.get_chat_log_channel(chat.id)
                if log_chat:
                    await send_log(context, log_chat, chat.id, result)

            return result

        return log_action

    def gloggable(func):
        @wraps(func)
        async def glog_action(
            update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
        ):
            result = await func(update, context, *args, **kwargs)
            chat = update.effective_chat
            message = update.effective_message

            if result:
                datetime_fmt = "%H:%M - %d-%m-%Y"
                result += f"\nEvent stamp: {datetime.utcnow().strftime(datetime_fmt)}"
                if chat.is_forum and chat.username:
                    result += f"\nLink: https://t.me/{chat.username}/{message.message_thread_id}/{message.message_id}"
                elif message.chat.type == chat.SUPERGROUP and message.chat.username:
                    result += (
                        f"\nLink: https://t.me/{chat.username}/{message.message_id}"
                    )
                log_chat = str(EVENT_LOGS)
                if log_chat:
                    await send_log(context, log_chat, chat.id, result)

            return result

        return glog_action

    async def send_log(
        context: ContextTypes.DEFAULT_TYPE,
        log_chat_id: str,
        orig_chat_id: str,
        result: str,
    ):
        bot = context.bot
        try:
            await bot.send_message(
                log_chat_id,
                result,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except BadRequest as excp:
            if excp.message == "Chat not found":
                try:
                    await bot.send_message(
                        orig_chat_id,
                        "This log channel has been deleted - unsetting.",
                        message_thread_id=1,
                    )
                except:
                    await bot.send_message(
                        orig_chat_id,
                        "This log channel has been deleted - unsetting.",
                    )
                sql.stop_chat_logging(orig_chat_id)
            else:
                LOGGER.warning(excp.message)
                LOGGER.warning(result)
                LOGGER.exception("Could not parse")

                await bot.send_message(
                    log_chat_id,
                    result
                    + "\n\nFormatting has been disabled due to an unexpected error.",
                )

    @check_admin(is_user=True)
    async def logging(update: Update, context: ContextTypes.DEFAULT_TYPE):
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat

        log_channel = sql.get_chat_log_channel(chat.id)
        if log_channel:
            log_channel_info = await bot.get_chat(log_channel)
            await message.reply_text(
                f"This group has all its logs sent to: {escape_markdown(log_channel_info.title)} (`{log_channel}`)",
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            await message.reply_text("No log channel has been set for this group!")

    @check_admin(is_user=True)
    async def setlog(update: Update, context: ContextTypes.DEFAULT_TYPE):
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat
        if chat.type == ChatType.CHANNEL:
            await bot.send_message(
                chat.id,
                "Now, forward the /setlog to the group you want to tie this channel to!",
            )

        elif message.forward_from_chat:
            sql.set_chat_log_channel(chat.id, message.forward_from_chat.id)

            try:
                await bot.send_message(
                    message.forward_from_chat.id,
                    f"This channel has been set as the log channel for {chat.title or chat.first_name}.",
                )
            except Forbidden as excp:
                if excp.message == "Forbidden: Bot is not a member of the channel chat":
                    if chat.is_forum:
                        await bot.send_message(
                            chat.id,
                            "Successfully set log channel!",
                            message_thread_id=message.message_thread_id,
                        )
                    else:
                        await bot.send_message(chat.id, "Successfully set log channel!")
                else:
                    LOGGER.exception("Error in setting the log channel.")

            if chat.is_forum:
                await bot.send_message(
                    chat.id,
                    "Successfully set log channel!",
                    message_thread_id=message.message_thread_id,
                )
            else:
                await bot.send_message(chat.id, "Successfully set log channel!")

        else:
            await message.reply_text(
                "The steps to set a log channel are:\n"
                " - Add bot to the desired channel (as an admin!)\n"
                " - Send /setlog in the channel\n"
                " - Forward the /setlog to the group\n",
            )

    @check_admin(is_user=True)
    async def unsetlog(update: Update, context: ContextTypes.DEFAULT_TYPE):
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat

        log_channel = sql.stop_chat_logging(chat.id)
        if log_channel:
            await bot.send_message(
                log_channel,
                f"Channel has been unlinked from {chat.title}",
            )
            await message.reply_text("Log channel has been un-set.")

        else:
            await message.reply_text("No log channel is set yet!")

    def __stats__():
        return f"• {sql.num_logchannels()} log channels set."

    def __migrate__(old_chat_id, new_chat_id):
        sql.migrate_chat(old_chat_id, new_chat_id)

    async def __chat_settings__(chat_id, user_id):
        log_channel = sql.get_chat_log_channel(chat_id)
        if log_channel:
            log_channel_info = await dispatcher.bot.get_chat(log_channel)
            return f"This group has all its logs sent to: {escape_markdown(log_channel_info.title)} (`{log_channel}`)"
        return "No log channel is set for this group!"

    # <=================================================== HELP ====================================================>

    __help__ = """
➠ *Admins Only*:

» /logchannel: Get log channel info.

» /setlog: Set the log channel.

» /unsetlog: Unset the log channel.

➠ *Setting the log channel is done by:*
➠ *Adding the bot to the desired channel (as an admin!)*

» Sending /setlog in the channel
» Forwarding the /setlog to the group
"""

    __mod_name__ = "LOG-SET"

    # <================================================ HANDLER =======================================================>
    function(CommandHandler("logchannel", logging, block=False))
    function(CommandHandler("setlog", setlog, block=False))
    function(CommandHandler("unsetlog", unsetlog, block=False))

else:
    # run anyway if module not loaded
    def loggable(func):
        return func

    def gloggable(func):
        return func


# <================================================ END =======================================================>
