import html
import json
import os
from typing import Optional

from telegram import Update
from telegram.ext import CommandHandler

from Mikobot import dispatcher
from Mikobot.plugins.helper_funcs.chat_status import dev_plus, sudo_plus
from Mikobot.plugins.helper_funcs.extraction import extract_user
from Mikobot.plugins.log_channel import gloggable

ELEVATED_USERS_FILE = os.path.join(os.getcwd(), "Mikobot/elevated_users.json")

DISASTER_LEVELS = {
    "Dragon": "DRAGONS",
    "Demon": "DEMONS",
    "Wolf": "WOLVES",
    "Tiger": "TIGERS",
}


async def check_user_id(user_id: int) -> Optional[str]:
    if not user_id:
        return "That...is a chat! baka ka omae?"
    return None


async def update_elevated_users(data):
    with open(ELEVATED_USERS_FILE, "w") as outfile:
        json.dump(data, outfile, indent=4)


async def add_disaster_level(update: Update, level: str, context) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = await extract_user(message, context, args)
    user_member = await bot.get_chat(user_id)
    rt = ""

    reply = await check_user_id(user_id)
    if reply:
        await message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    disaster_list = getattr(DISASTER_LEVELS, level)
    if user_id in disaster_list:
        await message.reply_text(f"This user is already a {level} Disaster.")
        return ""

    for disaster_level, disaster_users in DISASTER_LEVELS.items():
        if user_id in disaster_users:
            rt += f"Requested HA to promote this {disaster_level} to {level}."
            data[disaster_users].remove(user_id)
            setattr(DISASTER_LEVELS, disaster_level, disaster_users)

    data[DISASTER_LEVELS[level]].append(user_id)
    setattr(DISASTER_LEVELS, level, user_id)

    await update_effective_message.reply_text(
        rt
        + f"\nSuccessfully set Disaster level of {user_member.first_name} to {level}!"
    )

    log_message = (
        f"#{level.upper()}\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != "private":
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    await update.effective_message.reply_text(log_message)

    await update_elevated_users(data)


@dev_plus
@gloggable
async def addsudo(update: Update, context) -> str:
    await add_disaster_level(update, "Dragon", context)


@sudo_plus
@gloggable
async def addsupport(update: Update, context) -> str:
    await add_disaster_level(update, "Demon", context)


@sudo_plus
@gloggable
async def addwhitelist(update: Update, context) -> str:
    await add_disaster_level(update, "Wolf", context)


@sudo_plus
@gloggable
async def addtiger(update: Update, context) -> str:
    await add_disaster_level(update, "Tiger", context)


# Other functions can be refactored similarly...

SUDO_HANDLER = CommandHandler("addsudo", addsudo, block=False)
SUPPORT_HANDLER = CommandHandler(("addsupport", "adddemon"), addsupport, block=False)
TIGER_HANDLER = CommandHandler("addtiger", addtiger, block=False)
WHITELIST_HANDLER = CommandHandler(
    ("addwhitelist", "addwolf"), addwhitelist, block=False
)

dispatcher.add_handler(SUDO_HANDLER)
dispatcher.add_handler(SUPPORT_HANDLER)
dispatcher.add_handler(TIGER_HANDLER)
dispatcher.add_handler(WHITELIST_HANDLER)

__mod_name__ = "Devs"
__handlers__ = [
    SUDO_HANDLER,
    SUPPORT_HANDLER,
    TIGER_HANDLER,
    WHITELIST_HANDLER,
]
