# SOURCE https://github.com/Team-ProjectCodeX
# CREATED BY https://t.me/O_okarma
# PROVIDED BY https://t.me/ProjectCodeX

# <============================================== IMPORTS =========================================================>

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import CommandHandler, ContextTypes

from Mikobot import DEMONS, DEV_USERS, DRAGONS, LOGGER, OWNER_ID, WOLVES, function
from Mikobot.plugins.helper_funcs.chat_status import support_plus
from Mikobot.utils.parser import mention_html

# <=======================================================================================================>


# <================================================ FUNCTION =======================================================>
async def get_chat_member(context: ContextTypes.DEFAULT_TYPE, user_id):
    try:
        return await context.bot.get_chat_member(user_id, user_id)
    except TelegramError as e:
        LOGGER.error(f"Error getting chat member {user_id}: {e}")
        return None


async def get_user_info(context: ContextTypes.DEFAULT_TYPE, user_id):
    user_info = await get_chat_member(context, user_id)
    return user_info.user.first_name if user_info else "Unknown User"


async def get_users_info(context: ContextTypes.DEFAULT_TYPE, user_ids):
    return [(await get_user_info(context, user_id), user_id) for user_id in user_ids]


async def get_users_list(context: ContextTypes.DEFAULT_TYPE, user_ids):
    return [
        f"• {await mention_html(name, user_id)} (<code>{user_id}</code>)"
        for name, user_id in await get_users_info(context, user_ids)
    ]


@support_plus
async def botstaff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        owner = await get_chat_member(context, OWNER_ID)
        owner_info = await mention_html(owner.user.first_name, owner.user.id)
        reply = f"✪ <b>OWNER :</b> {owner_info} (<code>{OWNER_ID}</code>)\n"
    except TelegramError as e:
        LOGGER.error(f"Error getting owner information: {e}")
        reply = ""

    true_dev = list(set(DEV_USERS) - {OWNER_ID})
    reply += "\n\n➪ <b>SPECIAL GRADE USERS :</b>\n"
    reply += "\n".join(await get_users_list(context, true_dev)) or "No Dev Users"

    true_sudo = list(set(DRAGONS) - set(DEV_USERS))
    reply += "\n\n➪ <b>A GRADE USERS :</b>\n"
    reply += "\n".join(await get_users_list(context, true_sudo)) or "No Sudo Users"

    reply += "\n\n➪ <b>B GRADE USERS :</b>\n"
    reply += "\n".join(await get_users_list(context, DEMONS)) or "No Demon Users"

    reply += "\n\n➪ <b>NORMAL GRADE USERS :</b>\n"
    reply += (
        "\n".join(await get_users_list(context, WOLVES))
        or "No additional whitelisted users"
    )

    await update.message.reply_text(reply, parse_mode=ParseMode.HTML)
    LOGGER.info(
        f"{update.message.from_user.id} fetched botstaff in {update.message.chat.id}"
    )


# <================================================ HANDLER =======================================================>
function(CommandHandler("botadmins", botstaff, block=False))
# <================================================ END =======================================================>


# <=================================================== HELP ====================================================>
__help__ = """
➠ *BOT ADMINS ONLY:*

» /stats: Shows bot stats.

» /ping: see ping.

» /gban: Global ban.

» /gbanlist: Shows gban list.

» /botadmins: Opens Bot admin lists.

» /gcast: Advance broadcast system. Just reply to any message.

➠ *Write with text message*

» /broadcastall

» /broadcastusers

» /broadcastgroups
"""

__mod_name__ = "BOT-ADMIN"
# <================================================ HANDLER =======================================================>
