# <============================================== IMPORTS =========================================================>
import random
from datetime import datetime

from pyrogram import filters

from Database.mongodb.karma_mongo import get_couple, save_couple
from Mikobot import app

# <=======================================================================================================>


# <================================================ FUNCTION =======================================================>
def dt():
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M")
    dt_list = dt_string.split(" ")
    return dt_list


def dt_tom():
    a = (
        str(int(dt()[0].split("/")[0]) + 1)
        + "/"
        + dt()[0].split("/")[1]
        + "/"
        + dt()[0].split("/")[2]
    )
    return a


tomorrow = str(dt_tom())
today = str(dt()[0])

COUPLES_PIC = "https://telegra.ph/file/c6d0c884f559b9ed8a54e.jpg"
C = """
✧ 𝗖𝗢𝗨𝗣𝗟𝗘𝗦 𝗢𝗙 𝗧𝗛𝗘 𝗗𝗔𝗬 ✧
➖➖➖➖➖➖➖➖➖➖➖➖
{} + ( PGM🎀😶 (https://t.me/Chalnayaaaaaarr) + 花火 (https://t.me/zd_sr07) + ゼロツー (https://t.me/wewewe_x) ) = 💞
➖➖➖➖➖➖➖➖➖➖➖➖
𝗡𝗘𝗪 𝗖𝗢𝗨𝗣𝗟𝗘 𝗢𝗙 𝗧𝗛𝗘 𝗗𝗔𝗬 𝗖𝗔𝗡 𝗕𝗘 𝗖𝗛𝗢𝗦𝗘𝗡 𝗔𝗧 12AM {}
"""
CAP = """
✧ 𝗖𝗢𝗨𝗣𝗟𝗘𝗦 𝗢𝗙 𝗧𝗛𝗘 𝗗𝗔𝗬 ✧
➖➖➖➖➖➖➖➖➖➖➖➖
{} + {} = 💞
➖➖➖➖➖➖➖➖➖➖➖➖
𝗡𝗘𝗪 𝗖𝗢𝗨𝗣𝗟𝗘 𝗢𝗙 𝗧𝗛𝗘 𝗗𝗔𝗬 𝗖𝗔𝗡 𝗕𝗘 𝗖𝗛𝗢𝗦𝗘𝗡 𝗔𝗧 12AM {}
"""

CAP2 = """
✧ 𝗖𝗢𝗨𝗣𝗟𝗘𝗦 𝗢𝗙 𝗧𝗛𝗘 𝗗𝗔𝗬 ✧
➖➖➖➖➖➖➖➖➖➖➖➖
{} (tg://openmessage?user_id={}) + {} (tg://openmessage?user_id={}) = 💞\n
➖➖➖➖➖➖➖➖➖➖➖➖
𝗡𝗘𝗪 𝗖𝗢𝗨𝗣𝗟𝗘 𝗢𝗙 𝗧𝗛𝗘 𝗗𝗔𝗬 𝗖𝗔𝗡 𝗕𝗘 𝗖𝗛𝗢𝗦𝗘𝗡 𝗔𝗧 12AM {}
"""


@app.on_message(filters.command(["couple", "couples", "shipping"]) & ~filters.private)
async def nibba_nibbi(_, message):
    if message.from_user.id == 5540249238:
        my_ = await _.get_users("rfxtuv")
        me = await _.get_users(5540249238)
        await message.reply_photo(
            photo=COUPLES_PIC, caption=C.format(me.mention, tomorrow)
        )
    else:
        try:
            chat_id = message.chat.id
            is_selected = await get_couple(chat_id, today)
            if not is_selected:
                list_of_users = []
                async for i in _.get_chat_members(message.chat.id, limit=50):
                    if not i.user.is_bot:
                        list_of_users.append(i.user.id)
                if len(list_of_users) < 2:
                    return await message.reply_text("ɴᴏᴛ ᴇɴᴏᴜɢʜ ᴜsᴇʀs ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ.")
                c1_id = random.choice(list_of_users)
                c2_id = random.choice(list_of_users)
                while c1_id == c2_id:
                    c1_id = random.choice(list_of_users)
                c1_mention = (await _.get_users(c1_id)).mention
                c2_mention = (await _.get_users(c2_id)).mention
                await _.send_photo(
                    message.chat.id,
                    photo=COUPLES_PIC,
                    caption=CAP.format(c1_mention, c2_mention, tomorrow),
                )

                couple = {"c1_id": c1_id, "c2_id": c2_id}
                await save_couple(chat_id, today, couple)

            elif is_selected:
                c1_id = int(is_selected["c1_id"])
                c2_id = int(is_selected["c2_id"])

                c1_name = (await _.get_users(c1_id)).first_name
                c2_name = (await _.get_users(c2_id)).first_name
                print(c1_id, c2_id, c1_name, c2_name)
                couple_selection_message = f"""✧ 𝗖𝗢𝗨𝗣𝗟𝗘𝗦 𝗢𝗙 𝗧𝗛𝗘 𝗗𝗔𝗬 ✧
➖➖➖➖➖➖➖➖➖➖➖➖
[{c1_name}](tg://openmessage?user_id={c1_id}) + [{c2_name}](tg://openmessage?user_id={c2_id}) = 💞
➖➖➖➖➖➖➖➖➖➖➖➖
𝗡𝗘𝗪 𝗖𝗢𝗨𝗣𝗟𝗘 𝗢𝗙 𝗧𝗛𝗘 𝗗𝗔𝗬 𝗖𝗔𝗡 𝗕𝗘 𝗖𝗛𝗢𝗦𝗘𝗡 𝗔𝗧 12AM {tomorrow}"""
                await _.send_photo(
                    message.chat.id, photo=COUPLES_PIC, caption=couple_selection_message
                )
        except Exception as e:
            print(e)
            await message.reply_text(str(e))


# <=================================================== HELP ====================================================>


__help__ = """
💘 *Choose couples in your chat*

» /couple, /couples, /shipping *:* Choose 2 users and send their names as couples in your chat.
"""

__mod_name__ = "COUPLE"
# <================================================ END =======================================================>
