# <============================================== IMPORTS =========================================================>
import speedtest
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackQueryHandler, ContextTypes

from Mikobot import DEV_USERS, function
from Mikobot.plugins.disable import DisableAbleCommandHandler
from Mikobot.plugins.helper_funcs.chat_status import check_admin

# <=======================================================================================================>


# <================================================ FUNCTION =======================================================>
def convert(speed):
    return round(int(speed) / 1048576, 2)


@check_admin(only_dev=True)
async def speedtestxyz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [
            InlineKeyboardButton("Image", callback_data="speedtest_image"),
            InlineKeyboardButton("Text", callback_data="speedtest_text"),
        ],
    ]
    await update.effective_message.reply_text(
        "Select SpeedTest Mode",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def speedtestxyz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.from_user.id in DEV_USERS:
        msg = await update.effective_message.edit_text("Running a speedtest....")
        speed = speedtest.Speedtest()
        speed.get_best_server()
        speed.download()
        speed.upload()
        replymsg = "SpeedTest Results:"

        if query.data == "speedtest_image":
            speedtest_image = speed.results.share()
            await update.effective_message.reply_photo(
                photo=speedtest_image,
                caption=replymsg,
            )
            await msg.delete()

        elif query.data == "speedtest_text":
            result = speed.results.dict()
            replymsg += f"\nDownload: `{convert(result['download'])}Mb/s`\nUpload: `{convert(result['upload'])}Mb/s`\nPing: `{result['ping']}`"
            await update.effective_message.edit_text(
                replymsg, parse_mode=ParseMode.MARKDOWN
            )
    else:
        await query.answer("You are required to join Black Bulls to use this command.")


# <================================================ HANDLER =======================================================>
SPEED_TEST_HANDLER = DisableAbleCommandHandler("speedtest", speedtestxyz, block=False)
SPEED_TEST_CALLBACKHANDLER = CallbackQueryHandler(
    speedtestxyz_callback, pattern="speedtest_.*", block=False
)

function(SPEED_TEST_HANDLER)
function(SPEED_TEST_CALLBACKHANDLER)

__mod_name__ = "SpeedTest"
__command_list__ = ["speedtest"]
__handlers__ = [SPEED_TEST_HANDLER, SPEED_TEST_CALLBACKHANDLER]
# <================================================ END =======================================================>
