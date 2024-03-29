# https://github.com/Infamous-Hydra/YaeMiko
# https://github.com/Team-ProjectCodeX
# https://t.me/O_okarma

# <============================================== IMPORTS =========================================================>
from pyrogram.types import InlineKeyboardButton as ib
from telegram import InlineKeyboardButton

from Mikobot import BOT_USERNAME, OWNER_ID, SUPPORT_CHAT

# <============================================== CONSTANTS =========================================================>
START_IMG = [
    "https://telegra.ph/file/64c57e6d7e8ed3ebc35a4.jpg",
    "https://telegra.ph/file/8f06b80da69cf36020f7c.jpg",
    "https://telegra.ph/file/069d109e22cb4b94af802.jpg",

]

HEY_IMG = "https://telegra.ph/file/64c57e6d7e8ed3ebc35a4.jpg"

ALIVE_ANIMATION = [
    "https://telegra.ph/file/e15e6898c411e564c73c2.jpg",
    "https://telegra.ph/file/8b3452348019c2e42169c.jpg",
    "https://telegra.ph/file/069d109e22cb4b94af802.jpg",

]

FIRST_PART_TEXT = "✨ *ʜᴇʏ ᴛʜᴇʀᴇ!* `{}` . . ."

PM_START_TEXT = "✨ *ɪ ᴀᴍ ʏᴜᴋɪ, ᴀ ᴀɴɪᴍᴇ ᴛʜᴇᴍᴇᴅ ʙᴏᴛ ᴡʜɪᴄʜ ᴄᴀɴ ʜᴇʟᴘ ʏᴏᴜ ᴛᴏ ᴍᴀɴᴀɢᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴡɪᴛʜ ʙᴇsᴛ ɢʀᴏᴜᴘ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ sᴜᴘᴘᴏʀᴛ*"

START_BTN = [
    [
        InlineKeyboardButton(
            text="WANNA ADD ME (: ",
            url=f"https://t.me/{BOT_USERNAME}?startgroup=true",
        ),
    ],
    [
        InlineKeyboardButton(text="HELP", callback_data="help_back"),
    ],
    [
        InlineKeyboardButton(text="DETAILS", callback_data="Miko_"),
        InlineKeyboardButton(text="AI", callback_data="ai_handler"),
        InlineKeyboardButton(text="SOURCE", callback_data="git_source"),
    ],
    [
        InlineKeyboardButton(text="CREATOR", url=f"tg://user?id={OWNER_ID}"),
    ],
]

GROUP_START_BTN = [
    [
        InlineKeyboardButton(
            text="WANNA ADD ME (:",
            url=f"https://t.me/{BOT_USERNAME}?startgroup=true",
        ),
    ],
    [
        InlineKeyboardButton(text="SUPPORT", url=f"https://t.me/{SUPPORT_CHAT}"),
        InlineKeyboardButton(text="CREATOR", url=f"tg://user?id={OWNER_ID}"),
    ],
]

ALIVE_BTN = [
    [
        ib(text="UPDATES", url="https://t.me/paradoxbasement"),
    ],
    [
        ib(
            text="⇦ ADD ME ⇨",
            url=f"https://t.me/{BOT_USERNAME}?startgroup=true",
        ),
    ],
]

HELP_STRINGS = """
🫧 *Yuki-Onna* 🫧

☉ *Hᴇʀᴇ ᴀʀᴇ ᴀʟʟ ᴛʜᴇ ᴀᴠᴀɪʟᴀʙʟᴇ ᴄᴏᴍᴍᴀɴᴅs*

ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs ᴄᴀɴ ʙᴇ ᴜsᴇᴅ ᴡɪᴛʜ : /
"""
