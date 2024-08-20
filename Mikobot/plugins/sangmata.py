from pyrogram import filters
from pyrogram.types import Message

from Database.mongodb.sangmata_db import (
    add_userdata,
    cek_userdata,
    get_userdata,
    is_sangmata_on,
    sangmata_off,
    sangmata_on,
)
from Mikobot import app
from Mikobot.utils.can_restrict import can_restrict
from Mikobot.utils.custom_filters import PREFIX_HANDLER
from Mikobot.utils.localization import use_chat_lang


# Check user that change first_name, last_name and usernaname
@app.on_message(
    filters.group & ~filters.bot & ~filters.via_bot,
    group=5,
)
@use_chat_lang()
async def cek_mataa(_, ctx: Message, strings):
    if ctx.sender_chat or not await is_sangmata_on(ctx.chat.id):
        return
    if not await cek_userdata(ctx.from_user.id):
        return await add_userdata(
            ctx.from_user.id,
            ctx.from_user.username,
            ctx.from_user.first_name,
            ctx.from_user.last_name,
        )
    usernamebefore, first_name, lastname_before = await get_userdata(ctx.from_user.id)
    msg = ""
    if (
        usernamebefore != ctx.from_user.username
        or first_name != ctx.from_user.first_name
        or lastname_before != ctx.from_user.last_name
    ):
        msg += f"<b>➼ 𝗠𝗜𝗞𝗢 𝗠𝗔𝗧𝗔</b>\n\n🧑‍💼 User: {ctx.from_user.mention} [<code>{ctx.from_user.id}</code>]\n"
    if usernamebefore != ctx.from_user.username:
        usernamebefore = f"@{usernamebefore}" if usernamebefore else strings("no_uname")
        usernameafter = (
            f"@{ctx.from_user.username}"
            if ctx.from_user.username
            else strings("no_uname")
        )
        msg += strings("uname_change_msg").format(bef=usernamebefore, aft=usernameafter)
        await add_userdata(
            ctx.from_user.id,
            ctx.from_user.username,
            ctx.from_user.first_name,
            ctx.from_user.last_name,
        )
    if first_name != ctx.from_user.first_name:
        msg += strings("firstname_change_msg").format(
            bef=first_name, aft=ctx.from_user.first_name
        )
        await add_userdata(
            ctx.from_user.id,
            ctx.from_user.username,
            ctx.from_user.first_name,
            ctx.from_user.last_name,
        )
    if lastname_before != ctx.from_user.last_name:
        lastname_before = lastname_before or strings("no_last_name")
        lastname_after = ctx.from_user.last_name or strings("no_last_name")
        msg += strings("lastname_change_msg").format(
            bef=lastname_before, aft=lastname_after
        )
        await add_userdata(
            ctx.from_user.id,
            ctx.from_user.username,
            ctx.from_user.first_name,
            ctx.from_user.last_name,
        )
    if msg != "":
        await ctx.reply(msg, quote=False)


@app.on_message(
    filters.group
    & filters.command("imposter", PREFIX_HANDLER)
    & ~filters.bot
    & ~filters.via_bot
)
@can_restrict
@use_chat_lang()
async def set_mataa(_, ctx: Message, strings):
    if len(ctx.command) == 1:
        return await ctx.reply(strings("set_sangmata_help").format(cmd=ctx.command[0]))
    if ctx.command[1] == "on":
        cekset = await is_sangmata_on(ctx.chat.id)
        if cekset:
            await ctx.reply(strings("sangmata_already_on"))
        else:
            await sangmata_on(ctx.chat.id)
            await ctx.reply(strings("sangmata_enabled"))
    elif ctx.command[1] == "off":
        cekset = await is_sangmata_on(ctx.chat.id)
        if not cekset:
            await ctx.reply(strings("sangmata_already_off"))
        else:
            await sangmata_off(ctx.chat.id)
            await ctx.reply(strings("sangmata_disabled"))
    else:
        await ctx.reply(strings("wrong_param"))


# <=================================================== HELP ====================================================>
__help__ = """
🙅‍♂️ **Toji Mata**.

» /imposter : Detects if some one change his/her name.

» /imposter on : turns on toji mata.

» /imposter off : turns off toji mata.
"""

__mod_name__ = "IMPOSTER"
# <================================================ END =======================================================>
