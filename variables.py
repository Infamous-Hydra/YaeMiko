# https://github.com/Infamous-Hydra/YaeMiko
# https://github.com/Team-ProjectCodeX


class Config(object):
    # Configuration class for the bot

    # Enable or disable logging
    LOGGER = True

    # <================================================ REQUIRED ======================================================>
    # Telegram API configuration
    API_ID = 17513362  # Get this value from my.telegram.org/apps
    API_HASH = "54fa699f4c0944cb940fca908e2130f7"

    # Database configuration (PostgreSQL)
    DATABASE_URL = "postgres://pgcyxnql:Lc5Ix0fJpHJ3hIpkjLzUK8cy2KPEw564@hansken.db.elephantsql.com/pgcyxnql"

    # Event logs chat ID and message dump chat ID
    EVENT_LOGS = -1002092954715
    MESSAGE_DUMP = -1002092954715

    # MongoDB configuration
    MONGO_DB_URI = "mongodb+srv://ghost:ghost@3301@cluster0.nvpyoaf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

    # Support chat and support ID
    SUPPORT_CHAT = "Paradox Dumb"
    SUPPORT_ID = -1002092954715

    # Database name
    DB_NAME = "MikoDB"

    # Bot token
    TOKEN = "6841553936:AAFDcvQDqwLUUjPzfBKecIiV4LCKUfg14aY"  # Get bot token from @BotFather on Telegram

    # Owner's Telegram user ID (Must be an integer)
    OWNER_ID = 6498392569
    # <=======================================================================================================>

    # <================================================ OPTIONAL ======================================================>
    # Optional configuration fields

    # List of groups to blacklist
    BL_CHATS = []

    # User IDs of sudo users, dev users, support users, tiger users, and whitelist users
    DRAGONS = [6259443940]  # Sudo users
    DEV_USERS = [6259443940]  # Dev users
    DEMONS = [6259443940]  # Support users
    TIGERS = [6259443940]  # Tiger users
    WOLVES = [6259443940]  # Whitelist users

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