# SOURCE https://github.com/Team-ProjectCodeX
# CREATED BY https://t.me/O_okarma
# API BY https://www.github.com/SOME-1HING
# PROVIDED BY https://t.me/ProjectCodeX

# <============================================== IMPORTS =========================================================>
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from Mikobot import function
from Mikobot.state import state

# <=======================================================================================================>

# API URLs
CRICKET_API_URL = "https://sugoi-api.vercel.app/cricket"
FOOTBALL_API_URL = "https://sugoi-api.vercel.app/football"


# Define the MatchManager class as provided in your code
class MatchManager:
    def __init__(self, api_url):
        self.api_url = api_url
        self.matches = []
        self.match_count = 0

    async def fetch_matches(self):
        response = await state.get(self.api_url)
        self.matches = response.json()

    def get_next_matches(self, count):
        next_matches = self.matches[self.match_count : self.match_count + count]
        self.match_count += count
        return next_matches

    def reset_matches(self):
        self.matches = []
        self.match_count = 0


# <================================================ FUNCTION =======================================================>
async def get_match_text(match, sport):
    match_text = f"{'🏏' if sport == 'cricket' else '⚽️'} **{match['title']}**\n\n"
    match_text += f"🗓 *Date:* {match['date']}\n"
    match_text += f"🏆 *Team 1:* {match['team1']}\n"
    match_text += f"🏆 *Team 2:* {match['team2']}\n"
    match_text += f"🏟️ *Venue:* {match['venue']}"
    return match_text


def create_inline_keyboard(sport):
    inline_keyboard = [
        [
            InlineKeyboardButton(
                f"Next {sport.capitalize()} Match ➡️",
                callback_data=f"next_{sport}_match",
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard)


cricket_manager = MatchManager(CRICKET_API_URL)
football_manager = MatchManager(FOOTBALL_API_URL)


# Define a command handler for the /cricket command
async def get_cricket_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cricket_manager.reset_matches()
        await cricket_manager.fetch_matches()

        if not cricket_manager.matches:
            await update.message.reply_text("No cricket matches found.")
            return

        next_matches = cricket_manager.get_next_matches(1)
        match = next_matches[0]

        match_text = await get_match_text(match, "cricket")
        reply_markup = create_inline_keyboard("cricket")

        await update.message.reply_text(
            match_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")


# Define a command handler for the /football command
async def get_football_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        football_manager.reset_matches()
        await football_manager.fetch_matches()

        if not football_manager.matches:
            await update.message.reply_text("No football matches found.")
            return

        next_matches = football_manager.get_next_matches(1)
        match = next_matches[0]

        match_text = await get_match_text(match, "football")
        reply_markup = create_inline_keyboard("football")

        await update.message.reply_text(
            match_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")


# Define a callback query handler for showing the next match
async def show_next_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        sport = query.data.split("_")[1]
        manager = cricket_manager if sport == "cricket" else football_manager

        if not manager.matches:
            await query.answer(f"No more {sport} matches available.")
            return

        next_matches = manager.get_next_matches(3)

        if not next_matches:
            await query.answer(f"No more {sport} matches available.")
            return

        match_text = ""
        for match in next_matches:
            match_text += await get_match_text(match, sport) + "\n\n"

        reply_markup = create_inline_keyboard(sport)

        await query.message.edit_text(
            match_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        await query.answer()

    except Exception as e:
        await query.message.reply_text(f"An error occurred: {str(e)}")


# <=======================================================================================================>


# <================================================ HANDLER =======================================================>
# Add command handlers to the dispatcher
function(CommandHandler("cricket", get_cricket_matches))
function(CommandHandler("football", get_football_matches))
function(
    CallbackQueryHandler(show_next_match, pattern=r"^next_(cricket|football)_match$")
)

# <================================================= HELP ======================================================>
__help__ = """
🏅 *Match 𝗦chedule*

➠ *Commands*:

» /cricket: use this command to get information about the next cricket match.

» /football: use this command to get information about the next football match.
"""

__mod_name__ = "SPORTS"
# <================================================== END =====================================================>
