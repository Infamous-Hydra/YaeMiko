# https://github.com/Infamous-Hydra/YaeMiko
# https://github.com/Team-ProjectCodeX


class Config(object):
    # Configuration class for the bot

    # Enable or disable logging
    LOGGER = True

    # <================================================ REQUIRED ======================================================>
    # Telegram API configuration
    API_ID = 27240462      # Get this value from my.telegram.org/apps
    API_HASH = "e6d011e39e3e84cad1e417bda13c7dda"

    # Database configuration (PostgreSQL)
    DATABASE_URL = "postgres://sbnwcbdr:c0uxTz6sOeW2viw9GAmbpf3EkWIWo0LN@surus.db.elephantsql.com/sbnwcbdr"

    # Event logs chat ID and message dump chat ID
    EVENT_LOGS = -1001863937035
    MESSAGE_DUMP = -1001863937035

    # MongoDB configuration
    MONGO_DB_URI = "mongodb+srv://chrollodb:chrollodb@cluster0.fay8b9c.mongodb.net/?retryWrites=true&w=majority"

    # Support chat and support ID
    SUPPORT_CHAT = "EdgeBotSupport"
    SUPPORT_ID = -1001935569492

    # Database name
    DB_NAME = "Chrollo"

    # Bot token
    TOKEN = "6438153237:AAGqo8xu59eceX3oLShBXfEg4b5Nn9aWHBA"  # Get bot token from @BotFather on Telegram

    # Owner's Telegram user ID (Must be an integer)
    OWNER_ID = 6294805935
    # <=======================================================================================================>

    # <================================================ OPTIONAL ======================================================>
    # Optional configuration fields

    # List of groups to blacklist
    BL_CHATS = []

    # User IDs of sudo users, dev users, support users, tiger users, and whitelist users
    DRAGONS = []  # Sudo users
    DEV_USERS = []  # Dev users
    DEMONS = []  # Support users
    TIGERS = []  # Tiger users
    WOLVES = []  # Whitelist users

    # Toggle features
    ALLOW_CHATS = True
    ALLOW_EXCL = True
    DEL_CMDS = True
    INFOPIC = True

    # Modules to load or exclude
    LOAD = []
    NO_LOAD = []

    # Global ban settings
    STRICT_GBAN = True

    # Temporary download directory
    TEMP_DOWNLOAD_DIRECTORY = "./"
    # <=======================================================================================================>


# <=======================================================================================================>


class Production(Config):
    # Production configuration (inherits from Config)

    # Enable or disable logging
    LOGGER = True


class Development(Config):
    # Development configuration (inherits from Config)

    # Enable or disable logging
    LOGGER = True
