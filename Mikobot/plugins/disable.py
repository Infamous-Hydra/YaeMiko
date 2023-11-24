# <============================================== IMPORTS =========================================================>
import importlib
import re
from typing import Dict, List, Optional, Tuple, Union

from future.utils import string_types
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes, MessageHandler
from telegram.ext import filters as filters_module
from telegram.helpers import escape_markdown

from Mikobot import function
from Mikobot.plugins.helper_funcs.misc import is_module_loaded
from Mikobot.utils.cmdprefix import CMD_STARTERS

# <=======================================================================================================>

FILENAME = __name__.rsplit(".", 1)[-1]

# If module is due to be loaded, then setup all the magical handlers
if is_module_loaded(FILENAME):
    from Database.sql import disable_sql as sql
    from Mikobot.plugins.helper_funcs.chat_status import (
        check_admin,
        connection_status,
        is_user_admin,
    )

    DISABLE_CMDS = []
    DISABLE_OTHER = []
    ADMIN_CMDS = []

    # <================================================ CLASS =======================================================>
    class DisableAbleCommandHandler(CommandHandler):
        def __init__(
            self,
            command,
            callback,
            block: bool,
            filters: filters_module.BaseFilter = None,
            admin_ok=False,
        ):
            super().__init__(command, callback, block=block)
            self.admin_ok = admin_ok

            if isinstance(command, string_types):
                commands = frozenset({command.lower()})
                DISABLE_CMDS.append(command)
                if admin_ok:
                    ADMIN_CMDS.append(command)
            else:
                commands = frozenset(x.lower() for x in command)
                DISABLE_CMDS.extend(command)
                if admin_ok:
                    ADMIN_CMDS.extend(command)
            for comm in commands:
                if not re.match(r"^[\da-z_]{1,32}$", comm):
                    raise ValueError(f"Command `{comm}` is not a valid bot command")

            self.commands = commands
            self.filters = (
                filters if filters is not None else filters_module.UpdateType.MESSAGES
            )

        def check_update(
            self, update
        ) -> Optional[Union[bool, Tuple[List[str], Optional[Union[bool, Dict]]]]]:
            if isinstance(update, Update) and update.effective_message:
                message = update.effective_message

                if message.text and len(message.text) > 1:
                    fst_word = message.text.split(None, 1)[0]
                    if len(fst_word) > 1 and any(
                        fst_word.startswith(start) for start in CMD_STARTERS
                    ):
                        args = message.text.split()[1:]
                        command_parts = fst_word[1:].split("@")
                        command_parts.append(message.get_bot().username)

                        if not (
                            command_parts[0].lower() in self.commands
                            and command_parts[1].lower()
                            == message.get_bot().username.lower()
                        ):
                            return None

                        chat = update.effective_chat
                        user = update.effective_user

                        filter_result = self.filters.check_update(update)
                        if filter_result:
                            # disabled, admincmd, user admin
                            if sql.is_command_disabled(
                                chat.id, command_parts[0].lower()
                            ):
                                # check if command was disabled
                                is_disabled = command_parts[
                                    0
                                ] in ADMIN_CMDS and is_user_admin(chat, user.id)
                                if not is_disabled:
                                    return None
                                else:
                                    return args, filter_result

                            return args, filter_result
                        return False
                return None

    class DisableAbleMessageHandler(MessageHandler):
        def __init__(self, filters, callback, block: bool, friendly, **kwargs):
            super().__init__(filters, callback, block=block, **kwargs)
            DISABLE_OTHER.append(friendly)
            self.friendly = friendly
            if filters:
                self.filters = filters_module.UpdateType.MESSAGES & filters
            else:
                self.filters = filters_module.UpdateType.MESSAGES

        def check_update(self, update):
            chat = update.effective_chat
            message = update.effective_message
            filter_result = self.filters.check_update(update)

            try:
                args = message.text.split()[1:]
            except:
                args = []

            if super().check_update(update):
                if sql.is_command_disabled(chat.id, self.friendly):
                    return False
                else:
                    return args, filter_result

    # <=======================================================================================================>

    # <================================================ FUNCTION =======================================================>
    @connection_status
    @check_admin(is_user=True)
    async def disable(update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args
        chat = update.effective_chat
        if len(args) >= 1:
            disable_cmd = args[0]
            if disable_cmd.startswith(CMD_STARTERS):
                disable_cmd = disable_cmd[1:]

            if disable_cmd in set(DISABLE_CMDS + DISABLE_OTHER):
                sql.disable_command(chat.id, str(disable_cmd).lower())
                await update.effective_message.reply_text(
                    f"Disabled the use of `{disable_cmd}`",
                    parse_mode=ParseMode.MARKDOWN,
                )
            else:
                await update.effective_message.reply_text(
                    "That command can't be disabled"
                )

        else:
            await update.effective_message.reply_text("What should I disable?")

    @connection_status
    @check_admin(is_user=True)
    async def disable_module(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        args = context.args
        chat = update.effective_chat
        if len(args) >= 1:
            disable_module = "Mikobot.plugins." + args[0].rsplit(".", 1)[0]

            try:
                module = importlib.import_module(disable_module)
            except:
                await update.effective_message.reply_text(
                    "Does that module even exsist?"
                )
                return

            try:
                command_list = module.__command_list__
            except:
                await update.effective_message.reply_text(
                    "Module does not contain command list!",
                )
                return

            disabled_cmds = []
            failed_disabled_cmds = []

            for disable_cmd in command_list:
                if disable_cmd.startswith(CMD_STARTERS):
                    disable_cmd = disable_cmd[1:]

                if disable_cmd in set(DISABLE_CMDS + DISABLE_OTHER):
                    sql.disable_command(chat.id, str(disable_cmd).lower())
                    disabled_cmds.append(disable_cmd)
                else:
                    failed_disabled_cmds.append(disable_cmd)

            if disabled_cmds:
                disabled_cmds_string = ", ".join(disabled_cmds)
                await update.effective_message.reply_text(
                    f"Disabled the use of`{disabled_cmds_string}`",
                    parse_mode=ParseMode.MARKDOWN,
                )

            if failed_disabled_cmds:
                failed_disabled_cmds_string = ", ".join(failed_disabled_cmds)
                await update.effective_message.reply_text(
                    f"Commands `{failed_disabled_cmds_string}` can't be disabled",
                    parse_mode=ParseMode.MARKDOWN,
                )

        else:
            await update.effective_message.reply_text("What should I disable?")

    @connection_status
    @check_admin(is_user=True)
    async def enable(update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args
        chat = update.effective_chat
        if len(args) >= 1:
            enable_cmd = args[0]
            if enable_cmd.startswith(CMD_STARTERS):
                enable_cmd = enable_cmd[1:]

            if sql.enable_command(chat.id, enable_cmd):
                await update.effective_message.reply_text(
                    f"Enabled the use of`{enable_cmd}`",
                    parse_mode=ParseMode.MARKDOWN,
                )
            else:
                await update.effective_message.reply_text("Is that even disabled?")

        else:
            await update.effective_message.reply_text("What sould I enable?")

    @connection_status
    @check_admin(is_user=True)
    async def enable_module(update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args
        chat = update.effective_chat

        if len(args) >= 1:
            enable_module = "Mikobot.plugins." + args[0].rsplit(".", 1)[0]

            try:
                module = importlib.import_module(enable_module)
            except:
                await update.effective_message.reply_text(
                    "Does that module even exsist?"
                )
                return

            try:
                command_list = module.__command_list__
            except:
                await update.effective_message.reply_text(
                    "Module does not contain command list!",
                )
                return

            enabled_cmds = []
            failed_enabled_cmds = []

            for enable_cmd in command_list:
                if enable_cmd.startswith(CMD_STARTERS):
                    enable_cmd = enable_cmd[1:]

                if sql.enable_command(chat.id, enable_cmd):
                    enabled_cmds.append(enable_cmd)
                else:
                    failed_enabled_cmds.append(enable_cmd)

            if enabled_cmds:
                enabled_cmds_string = ", ".join(enabled_cmds)
                await update.effective_message.reply_text(
                    f"Enabled the use of`{enabled_cmds_string}`",
                    parse_mode=ParseMode.MARKDOWN,
                )

            if failed_enabled_cmds:
                failed_enabled_cmds_string = ", ".join(failed_enabled_cmds)
                await update.effective_message.reply_text(
                    f"Are the commands `{failed_enabled_cmds_string}` even disabled?",
                    parse_mode=ParseMode.MARKDOWN,
                )

        else:
            await update.effective_message.reply_text("ᴡʜᴀᴛ sʜᴏᴜʟᴅ I ᴇɴᴀʙʟᴇ?")

    @connection_status
    @check_admin(is_user=True)
    async def list_cmds(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if DISABLE_CMDS + DISABLE_OTHER:
            result = ""
            for cmd in set(DISABLE_CMDS + DISABLE_OTHER):
                result += f" - `{escape_markdown(cmd)}`\n"
            await update.effective_message.reply_text(
                f"The following commands are toggleable:\n{result}",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            await update.effective_message.reply_text("No commands can be disabled.")

    # do not async
    def build_curr_disabled(chat_id: Union[str, int]) -> str:
        disabled = sql.get_all_disabled(chat_id)
        if not disabled:
            return "No commands are disabled!"

        result = ""
        for cmd in disabled:
            result += " - `{}`\n".format(escape_markdown(cmd))
        return "The following commands are currently restricted:\n{}".format(result)

    @connection_status
    async def commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat
        await update.effective_message.reply_text(
            build_curr_disabled(chat.id),
            parse_mode=ParseMode.MARKDOWN,
        )

    def __stats__():
        return f"• {sql.num_disabled()} disabled items, across {sql.num_chats()} chats."

    def __migrate__(old_chat_id, new_chat_id):
        sql.migrate_chat(old_chat_id, new_chat_id)

    def __chat_settings__(chat_id, user_id):
        return build_curr_disabled(chat_id)

    # <=================================================== HANDLER ====================================================>

    DISABLE_HANDLER = CommandHandler("disable", disable, block=False)
    DISABLE_MODULE_HANDLER = CommandHandler(
        "disablemodule", disable_module, block=False
    )
    ENABLE_HANDLER = CommandHandler("enable", enable, block=False)
    ENABLE_MODULE_HANDLER = CommandHandler("enablemodule", enable_module, block=False)
    COMMANDS_HANDLER = CommandHandler(["cmds", "disabled"], commands, block=False)
    TOGGLE_HANDLER = CommandHandler("listcmds", list_cmds, block=False)

    function(DISABLE_HANDLER)
    function(DISABLE_MODULE_HANDLER)
    function(ENABLE_HANDLER)
    function(ENABLE_MODULE_HANDLER)
    function(COMMANDS_HANDLER)
    function(TOGGLE_HANDLER)

    # <=================================================== HELP ====================================================>
    __help__ = """
» /cmds: Check the current status of disabled commands

➠ *Admins only*:

» /enable < cmd name >: Enable that command.

» /disable < cmd name >: Disable that command.

» /enablemodule < module name >: Enable all commands in that module.

» /disablemodule < module name >: Disable all commands in that module.

» /listcmds: List all possible toggleable commands.
    """

    __mod_name__ = "DISABLE"

else:
    DisableAbleCommandHandler = CommandHandler
    DisableAbleMessageHandler = MessageHandler
# <================================================ END =======================================================>
