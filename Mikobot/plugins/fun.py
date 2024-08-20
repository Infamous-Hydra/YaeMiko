# <============================================== IMPORTS =========================================================>
import random

from pyjokes import get_joke
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import Mikobot.utils.fun_strings as fun_strings
from Mikobot import function
from Mikobot.events import register
from Mikobot.plugins.disable import DisableAbleCommandHandler
from Mikobot.state import state

# <=======================================================================================================>


# <================================================ FUNCTION =======================================================>
async def make_request(url: str) -> str:
    response = await state.get(url)
    response.raise_for_status()
    return response.json()["question"]


async def truth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    truth_question = await make_request("https://api.truthordarebot.xyz/v1/truth")
    await update.effective_message.reply_text(truth_question)


async def dare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dare_question = await make_request("https://api.truthordarebot.xyz/v1/dare")
    await update.effective_message.reply_text(dare_question)


@register(pattern="^/joke ?(.*)")
async def joke(event):
    await event.reply(get_joke())


async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(range(1, 7)))


async def flirt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    await update.effective_message.reply_text(random.choice(fun_strings.FLIRT))


async def toss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(fun_strings.TOSS))


async def shrug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    reply_text = (
        msg.reply_to_message.reply_text if msg.reply_to_message else msg.reply_text
    )
    await reply_text(r"¯\_(ツ)_/¯")


async def bluetext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    reply_text = (
        msg.reply_to_message.reply_text if msg.reply_to_message else msg.reply_text
    )
    await reply_text(
        "/BLUE /TEXT\n/MUST /CLICK\n/I /AM /A /STUPID /ANIMAL /THAT /IS /ATTRACTED /TO /COLORS"
    )


async def rlg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    eyes = random.choice(fun_strings.EYES)
    mouth = random.choice(fun_strings.MOUTHS)
    ears = random.choice(fun_strings.EARS)

    if len(eyes) == 2:
        repl = ears[0] + eyes[0] + mouth[0] + eyes[1] + ears[1]
    else:
        repl = ears[0] + eyes[0] + mouth[0] + eyes[0] + ears[1]
    await update.message.reply_text(repl)


async def decide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_text = (
        update.effective_message.reply_to_message.reply_text
        if update.effective_message.reply_to_message
        else update.effective_message.reply_text
    )
    await reply_text(random.choice(fun_strings.DECIDE))


normiefont = [
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
]

weebyfont = [
    "卂",
    "乃",
    "匚",
    "刀",
    "乇",
    "下",
    "厶",
    "卄",
    "工",
    "丁",
    "长",
    "乚",
    "从",
    "𠘨",
    "口",
    "尸",
    "㔿",
    "尺",
    "丂",
    "丅",
    "凵",
    "リ",
    "山",
    "乂",
    "丫",
    "乙",
]


async def webify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    message = update.effective_message
    string = ""

    if message.reply_to_message:
        string = message.reply_to_message.text.lower().replace(" ", "  ")

    if args:
        string = "  ".join(args).lower()

    if not string:
        await message.reply_text(
            "Usage is `/weebify <text>`", parse_mode=ParseMode.MARKDOWN
        )
        return

    for normiecharacter in string:
        if normiecharacter in normiefont:
            weebycharacter = weebyfont[normiefont.index(normiecharacter)]
            string = string.replace(normiecharacter, weebycharacter)

    if message.reply_to_message:
        await message.reply_to_message.reply_text(string)
    else:
        await message.reply_text(string)


# <=================================================== HELP ====================================================>


__help__ = """
» /cosplay: sends cosplay images.

» /decide: randomly answers yes/no/maybe.

» /truth: sends a random truth string.

» /dare: sends a random dare string.

» /toss: tosses a coin.

» /shrug: get shrug xd.

» /bluetext: check yourself :V.

» /roll: roll a dice.

» /rlg: join ears, nose, mouth and create an emo ;-;

» /weebify <text>: returns a weebified text.

» /flirt <text>: returns a flirt text.

» /joke <text>: tells a random joke.
"""

# <================================================ HANDLER =======================================================>
ROLL_HANDLER = DisableAbleCommandHandler("roll", roll, block=False)
TOSS_HANDLER = DisableAbleCommandHandler("toss", toss, block=False)
SHRUG_HANDLER = DisableAbleCommandHandler("shrug", shrug, block=False)
BLUETEXT_HANDLER = DisableAbleCommandHandler("bluetext", bluetext, block=False)
RLG_HANDLER = DisableAbleCommandHandler("rlg", rlg, block=False)
DECIDE_HANDLER = DisableAbleCommandHandler("decide", decide, block=False)
WEEBIFY_HANDLER = DisableAbleCommandHandler("weebify", webify, block=False)
FLIRT_HANDLER = DisableAbleCommandHandler("flirt", flirt, block=False)
TRUTH_HANDLER = DisableAbleCommandHandler("truth", truth, block=False)
DARE_HANDLER = DisableAbleCommandHandler("dare", dare, block=False)

function(WEEBIFY_HANDLER)
function(ROLL_HANDLER)
function(TOSS_HANDLER)
function(SHRUG_HANDLER)
function(BLUETEXT_HANDLER)
function(RLG_HANDLER)
function(DECIDE_HANDLER)
function(FLIRT_HANDLER)
function(TRUTH_HANDLER)
function(DARE_HANDLER)

__mod_name__ = "FUN"
__command_list__ = [
    "roll",
    "toss",
    "shrug",
    "bluetext",
    "rlg",
    "decide",
    "cosplay",
    "weebify",
    "flirt",
    "truth",
    "dare",
]
__handlers__ = [
    ROLL_HANDLER,
    TOSS_HANDLER,
    SHRUG_HANDLER,
    BLUETEXT_HANDLER,
    RLG_HANDLER,
    DECIDE_HANDLER,
    WEEBIFY_HANDLER,
    FLIRT_HANDLER,
    TRUTH_HANDLER,
    DARE_HANDLER,
]
# <================================================ END =======================================================>
