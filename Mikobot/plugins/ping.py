# <============================================== IMPORTS =========================================================>
import time

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from Mikobot import StartTime, function
from Mikobot.__main__ import get_readable_time
from Mikobot.plugins.helper_funcs.chat_status import check_admin

# <=======================================================================================================>


# <================================================ FUNCTION =======================================================>
@check_admin(only_dev=True)
async def ptb_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    start_time = time.time()
    message = await msg.reply_text("Pining")
    end_time = time.time()
    telegram_ping = str(round((end_time - start_time) * 1000, 3)) + " ms"
    uptime = get_readable_time((time.time() - StartTime))

    await message.edit_text(
        "🏓 <b>PONG</b>\n\n"
        "<b>Time taken:</b> <code>{}</code>\n"
        "<b>Uptime:</b> <code>{}</code>".format(telegram_ping, uptime),
        parse_mode=ParseMode.HTML,
    )


# <=======================================================================================================>


# <================================================ HANDLER =======================================================>
function(CommandHandler("ping", ptb_ping, block=False))
# <================================================ END =======================================================>
