# <============================================== IMPORTS =========================================================>
import re
from datetime import datetime, timedelta

from pyrogram import filters
from pyrogram.types import ChatPermissions

from Database.mongodb.blacklistdb import (
    delete_blacklist_filter,
    get_blacklisted_words,
    save_blacklist_filter,
)
from Mikobot import DRAGONS, app
from Mikobot.utils.errors import capture_err
from Mikobot.utils.permissions import adminsOnly, list_admins

# <=======================================================================================================>

blacklist_filters_group = 8


# <================================================ FUNCTION =======================================================>
@app.on_message(filters.command("blacklist") & ~filters.private)
@adminsOnly("can_restrict_members")
async def save_filters(_, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage:\n/blacklist [WORD|SENTENCE]")
    word = message.text.split(None, 1)[1].strip()
    if not word:
        return await message.reply_text("**Usage**\n__/blacklist [WORD|SENTENCE]__")
    chat_id = message.chat.id
    await save_blacklist_filter(chat_id, word)
    await message.reply_text(f"__**Blacklisted {word}.**__")


@app.on_message(filters.command("blacklisted") & ~filters.private)
@capture_err
async def get_filterss(_, message):
    data = await get_blacklisted_words(message.chat.id)
    if not data:
        await message.reply_text("**No blacklisted words in this chat.**")
    else:
        msg = f"List of blacklisted words in {message.chat.title} :\n"
        for word in data:
            msg += f"**-** `{word}`\n"
        await message.reply_text(msg)


@app.on_message(filters.command("whitelist") & ~filters.private)
@adminsOnly("can_restrict_members")
async def del_filter(_, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage:\n/whitelist [WORD|SENTENCE]")
    word = message.text.split(None, 1)[1].strip()
    if not word:
        return await message.reply_text("Usage:\n/whitelist [WORD|SENTENCE]")
    chat_id = message.chat.id
    deleted = await delete_blacklist_filter(chat_id, word)
    if deleted:
        return await message.reply_text(f"**Whitelisted {word}.**")
    await message.reply_text("**No such blacklist filter.**")


@app.on_message(filters.text & ~filters.private, group=blacklist_filters_group)
@capture_err
async def blacklist_filters_re(_, message):
    text = message.text.lower().strip()
    if not text:
        return
    chat_id = message.chat.id
    user = message.from_user
    if not user:
        return
    if user.id in DRAGONS:
        return
    list_of_filters = await get_blacklisted_words(chat_id)
    for word in list_of_filters:
        pattern = r"( |^|[^\w])" + re.escape(word) + r"( |$|[^\w])"
        if re.search(pattern, text, flags=re.IGNORECASE):
            if user.id in await list_admins(chat_id):
                return
            try:
                await message.delete()
                await message.chat.restrict_member(
                    user.id,
                    ChatPermissions(),
                    until_date=datetime.now() + timedelta(minutes=60),
                )
            except Exception:
                return
            return await app.send_message(
                chat_id,
                f"Muted {user.mention} [`{user.id}`] for 1 hour "
                + f"due to a blacklist match on {word}.",
            )


# <=================================================== HELP ====================================================>


__help__ = """
❌ *Get your word/sentence blacklisted*

» /blacklisted - Get All The Blacklisted Words In The Chat.

» /blacklist [WORD|SENTENCE] - Blacklist A Word Or A Sentence.

» /whitelist [WORD|SENTENCE] - Whitelist A Word Or A Sentence.
"""

__mod_name__ = "BLACKLIST"
# <================================================ END =======================================================>
