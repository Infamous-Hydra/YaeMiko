import html

from alphabet_detector import AlphabetDetector
from telegram import (
    Chat,
    ChatMemberAdministrator,
    ChatPermissions,
    MessageEntity,
    Update,
)
from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters
from telegram.helpers import mention_html

import Database.sql.locks_sql as sql
from Database.sql.approve_sql import is_approved
from Mikobot import DRAGONS, LOGGER, dispatcher, function
from Mikobot.plugins.connection import connected
from Mikobot.plugins.disable import DisableAbleCommandHandler
from Mikobot.plugins.helper_funcs.alternate import send_message, typing_action
from Mikobot.plugins.helper_funcs.chat_status import (
    check_admin,
    is_bot_admin,
    user_not_admin,
)
from Mikobot.plugins.log_channel import loggable

ad = AlphabetDetector()

LOCK_TYPES = {
    "audio": filters.AUDIO,
    "voice": filters.VOICE,
    "document": filters.Document.ALL,
    "video": filters.VIDEO,
    "contact": filters.CONTACT,
    "photo": filters.PHOTO,
    "url": filters.Entity(MessageEntity.URL) | filters.CaptionEntity(MessageEntity.URL),
    "bots": filters.StatusUpdate.NEW_CHAT_MEMBERS,
    "forward": filters.FORWARDED,
    "game": filters.GAME,
    "location": filters.LOCATION,
    "egame": filters.Dice.ALL,
    "rtl": "rtl",
    "button": "button",
    "inline": "inline",
    "phone": filters.Entity(MessageEntity.PHONE_NUMBER)
    | filters.CaptionEntity(MessageEntity.PHONE_NUMBER),
    "command": filters.COMMAND,
    "email": filters.Entity(MessageEntity.EMAIL)
    | filters.CaptionEntity(MessageEntity.EMAIL),
    "anonchannel": "anonchannel",
    "forwardchannel": "forwardchannel",
    "forwardbot": "forwardbot",
    # "invitelink": ,
    "videonote": filters.VIDEO_NOTE,
    "emojicustom": filters.Entity(MessageEntity.CUSTOM_EMOJI)
    | filters.CaptionEntity(MessageEntity.CUSTOM_EMOJI),
    "stickerpremium": filters.Sticker.PREMIUM,
    "stickeranimated": filters.Sticker.ANIMATED,
}

LOCK_CHAT_RESTRICTION = {
    "all": {
        "can_send_messages": False,
        "can_send_media_messages": False,
        "can_send_polls": False,
        "can_send_other_messages": False,
        "can_add_web_page_previews": False,
        "can_change_info": False,
        "can_invite_users": False,
        "can_pin_messages": False,
        "can_manage_topics": False,
    },
    "messages": {"can_send_messages": False},
    "media": {"can_send_media_messages": False},
    "sticker": {"can_send_other_messages": False},
    "gif": {"can_send_other_messages": False},
    "poll": {"can_send_polls": False},
    "other": {"can_send_other_messages": False},
    "previews": {"can_add_web_page_previews": False},
    "info": {"can_change_info": False},
    "invite": {"can_invite_users": False},
    "pin": {"can_pin_messages": False},
    "topics": {"can_manage_topics": False},
}

UNLOCK_CHAT_RESTRICTION = {
    "all": {
        "can_send_messages": True,
        "can_send_media_messages": True,
        "can_send_polls": True,
        "can_send_other_messages": True,
        "can_add_web_page_previews": True,
        "can_invite_users": True,
        "can_manage_topics": True,
    },
    "messages": {"can_send_messages": True},
    "media": {"can_send_media_messages": True},
    "sticker": {"can_send_other_messages": True},
    "gif": {"can_send_other_messages": True},
    "poll": {"can_send_polls": True},
    "other": {"can_send_other_messages": True},
    "previews": {"can_add_web_page_previews": True},
    "info": {"can_change_info": True},
    "invite": {"can_invite_users": True},
    "pin": {"can_pin_messages": True},
    "topics": {"can_manage_topics": True},
}

PERM_GROUP = 1
REST_GROUP = 2


# NOT ASYNC
async def restr_members(
    bot,
    chat_id,
    members,
    messages=False,
    media=False,
    other=False,
    previews=False,
):
    for mem in members:
        if mem.user in DRAGONS:
            pass
        elif mem.user == 777000 or mem.user == 1087968824:
            pass
        try:
            await bot.restrict_chat_member(
                chat_id,
                mem.user,
                permissions=ChatPermissions(
                    can_send_messages=messages,
                    can_send_media_messages=media,
                    can_send_other_messages=other,
                    can_add_web_page_previews=previews,
                ),
            )
        except TelegramError:
            pass


# NOT ASYNC
async def unrestr_members(
    bot,
    chat_id,
    members,
    messages=True,
    media=True,
    other=True,
    previews=True,
):
    for mem in members:
        try:
            await bot.restrict_chat_member(
                chat_id,
                mem.user,
                permissions=ChatPermissions(
                    can_send_messages=messages,
                    can_send_media_messages=media,
                    can_send_other_messages=other,
                    can_add_web_page_previews=previews,
                ),
            )
        except TelegramError:
            pass


async def locktypes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "\n • ".join(
            ["Locks available: "]
            + sorted(list(LOCK_TYPES) + list(LOCK_CHAT_RESTRICTION)),
        ),
    )


@check_admin(permission="can_delete_messages", is_both=True)
@loggable
@typing_action
async def lock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    args = context.args
    chat = update.effective_chat
    user = update.effective_user

    if len(args) >= 1:
        ltype = args[0].lower()
        if ltype in LOCK_TYPES:
            # Connection check
            conn = await connected(context.bot, update, chat, user.id, need_admin=True)
            if conn:
                chat = await dispatcher.bot.getChat(conn)
                chat_id = conn
                chat_name = chat.title
                text = "Locked {} for non-admins in {}!".format(ltype, chat_name)
            else:
                if update.effective_message.chat.type == "private":
                    await send_message(
                        update.effective_message,
                        "This command is meant to use in group not in PM",
                    )
                    return ""
                chat = update.effective_chat
                chat_id = update.effective_chat.id
                chat_name = update.effective_message.chat.title
                text = "Locked {} for non-admins!".format(ltype)
            sql.update_lock(chat.id, ltype, locked=True)
            await send_message(update.effective_message, text, parse_mode="markdown")

            return (
                "<b>{}:</b>"
                "\n#LOCK"
                "\n<b>Admin:</b> {}"
                "\nLocked <code>{}</code>.".format(
                    html.escape(chat.title),
                    mention_html(user.id, user.first_name),
                    ltype,
                )
            )

        elif ltype in LOCK_CHAT_RESTRICTION:
            # Connection check
            conn = await connected(context.bot, update, chat, user.id, need_admin=True)
            if conn:
                chat = await dispatcher.bot.getChat(conn)
                chat_id = conn
                chat_name = chat.title
                text = "Locked {} for all non-admins in {}!".format(
                    ltype,
                    chat_name,
                )
            else:
                if update.effective_message.chat.type == "private":
                    await send_message(
                        update.effective_message,
                        "This command is meant to use in group not in PM",
                    )
                    return ""
                chat = update.effective_chat
                chat_id = update.effective_chat.id
                chat_name = update.effective_message.chat.title
                text = "Locked {} for all non-admins!".format(ltype)

            chat_obj = await context.bot.getChat(chat_id)
            current_permission = chat_obj.permissions
            await context.bot.set_chat_permissions(
                chat_id=chat_id,
                permissions=get_permission_list(
                    current_permission.to_dict(),
                    LOCK_CHAT_RESTRICTION[ltype.lower()],
                ),
            )

            await context.bot.restrict_chat_member(
                chat.id,
                int(777000),
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                ),
            )

            await context.bot.restrict_chat_member(
                chat.id,
                int(1087968824),
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                ),
            )

            await send_message(update.effective_message, text, parse_mode="markdown")
            return (
                "<b>{}:</b>"
                "\n#Permission_LOCK"
                "\n<b>Admin:</b> {}"
                "\nLocked <code>{}</code>.".format(
                    html.escape(chat.title),
                    mention_html(user.id, user.first_name),
                    ltype,
                )
            )

        else:
            await send_message(
                update.effective_message,
                "What are you trying to lock...? Try /locktypes for the list of lockables",
            )
    else:
        await send_message(update.effective_message, "What are you trying to lock...?")

    return ""


@check_admin(permission="can_delete_messages", is_both=True)
@loggable
@typing_action
async def unlock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if len(args) >= 1:
        ltype = args[0].lower()
        if ltype in LOCK_TYPES:
            # Connection check
            conn = await connected(context.bot, update, chat, user.id, need_admin=True)
            if conn:
                chat = await dispatcher.bot.getChat(conn)
                chat_id = conn
                chat_name = chat.title
                text = "Unlocked {} for everyone in {}!".format(ltype, chat_name)
            else:
                if update.effective_message.chat.type == "private":
                    await send_message(
                        update.effective_message,
                        "This command is meant to use in group not in PM",
                    )
                    return ""
                chat = update.effective_chat
                chat_id = update.effective_chat.id
                chat_name = update.effective_message.chat.title
                text = "Unlocked {} for everyone!".format(ltype)
            sql.update_lock(chat.id, ltype, locked=False)
            await send_message(update.effective_message, text, parse_mode="markdown")
            return (
                "<b>{}:</b>"
                "\n#UNLOCK"
                "\n<b>Admin:</b> {}"
                "\nUnlocked <code>{}</code>.".format(
                    html.escape(chat.title),
                    mention_html(user.id, user.first_name),
                    ltype,
                )
            )

        elif ltype in UNLOCK_CHAT_RESTRICTION:
            # Connection check
            conn = await connected(context.bot, update, chat, user.id, need_admin=True)
            if conn:
                chat = await dispatcher.bot.getChat(conn)
                chat_id = conn
                chat_name = chat.title
                text = "Unlocked {} for everyone in {}!".format(ltype, chat_name)
            else:
                if update.effective_message.chat.type == "private":
                    await send_message(
                        update.effective_message,
                        "This command is meant to use in group not in PM",
                    )
                    return ""
                chat = update.effective_chat
                chat_id = update.effective_chat.id
                chat_name = update.effective_message.chat.title
                text = "Unlocked {} for everyone!".format(ltype)

            member = await chat.get_member(context.bot.id)

            if isinstance(member, ChatMemberAdministrator):
                can_change_info = member.can_change_info
            else:
                can_change_info = True

            if not can_change_info:
                await send_message(
                    update.effective_message,
                    "I don't have permission to change group info.",
                    parse_mode="markdown",
                )
                return

            chat_obj = await context.bot.getChat(chat_id)
            current_permission = chat_obj.permissions
            await context.bot.set_chat_permissions(
                chat_id=chat_id,
                permissions=get_permission_list(
                    current_permission.to_dict(),
                    UNLOCK_CHAT_RESTRICTION[ltype.lower()],
                ),
            )

            await send_message(update.effective_message, text, parse_mode="markdown")

            return (
                "<b>{}:</b>"
                "\n#UNLOCK"
                "\n<b>Admin:</b> {}"
                "\nUnlocked <code>{}</code>.".format(
                    html.escape(chat.title),
                    mention_html(user.id, user.first_name),
                    ltype,
                )
            )
        else:
            await send_message(
                update.effective_message,
                "What are you trying to unlock...? Try /locktypes for the list of lockables.",
            )

    else:
        await send_message(
            update.effective_message, "What are you trying to unlock...?"
        )


@user_not_admin
@check_admin(permission="can_delete_messages", is_bot=True, no_reply=True)
async def del_lockables(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user
    if is_approved(chat.id, user.id):
        return
    for lockable, filter in LOCK_TYPES.items():
        if lockable == "rtl":
            if sql.is_locked(chat.id, lockable):
                if message.caption:
                    check = ad.detect_alphabet("{}".format(message.caption))
                    if "ARABIC" in check:
                        try:
                            await message.delete()
                        except BadRequest as excp:
                            if excp.message == "Message to delete not found":
                                pass
                            else:
                                LOGGER.exception("ERROR in lockables - rtl:caption")
                        break
                if message.text:
                    check = ad.detect_alphabet("{}".format(message.text))
                    if "ARABIC" in check:
                        try:
                            await message.delete()
                        except BadRequest as excp:
                            if excp.message == "Message to delete not found":
                                pass
                            else:
                                LOGGER.exception("ERROR in lockables - rtl:text")
                        break
            continue
        if lockable == "button":
            if sql.is_locked(chat.id, lockable):
                if message.reply_markup and message.reply_markup.inline_keyboard:
                    try:
                        await message.delete()
                    except BadRequest as excp:
                        if excp.message == "Message to delete not found":
                            pass
                        else:
                            LOGGER.exception("ERROR in lockables - button")
                    break
            continue
        if lockable == "inline":
            if sql.is_locked(chat.id, lockable):
                if message and message.via_bot:
                    try:
                        await message.delete()
                    except BadRequest as excp:
                        if excp.message == "Message to delete not found":
                            pass
                        else:
                            LOGGER.exception("ERROR in lockables - inline")
                    break
            continue
        if lockable == "forwardchannel":
            if sql.is_locked(chat.id, lockable):
                if message.forward_from_chat:
                    if message.forward_from_chat.type == "channel":
                        try:
                            await message.delete()
                        except BadRequest as excp:
                            if excp.message == "Message to delete not found":
                                pass
                            else:
                                LOGGER.exception("ERROR in lockables - forwardchannel")
                        break
                continue
            continue
        if lockable == "forwardbot":
            if sql.is_locked(chat.id, lockable):
                if message.forward_from:
                    if message.forward_from.is_bot:
                        try:
                            await message.delete()
                        except BadRequest as excp:
                            if excp.message == "Message to delete not found":
                                pass
                            else:
                                LOGGER.exception("ERROR in lockables - forwardchannel")
                        break
                continue
            continue
        if lockable == "anonchannel":
            if sql.is_locked(chat.id, lockable):
                if message.from_user:
                    if message.from_user.id == 136817688:
                        try:
                            await message.delete()
                        except BadRequest as excp:
                            if excp.message == "Message to delete not found":
                                pass
                            else:
                                LOGGER.exception("ERROR in lockables - anonchannel")
                        break
                continue
            continue
        if filter.check_update(update) and sql.is_locked(chat.id, lockable):
            if lockable == "bots":
                new_members = update.effective_message.new_chat_members
                for new_mem in new_members:
                    if new_mem.is_bot:
                        if not await is_bot_admin(chat, context.bot.id):
                            await send_message(
                                update.effective_message,
                                "I see a bot and I've been told to stop them from joining..."
                                "but I'm not admin!",
                            )
                            return

                        await chat.ban_member(new_mem.id)
                        await send_message(
                            update.effective_message,
                            "Only admins are allowed to add bots in this chat! Get outta here.",
                        )
                        break
            else:
                try:
                    await message.delete()
                except BadRequest as excp:
                    if excp.message == "Message to delete not found":
                        pass
                    else:
                        LOGGER.exception("ERROR in lockables")

                break


async def build_lock_message(chat_id):
    locks = sql.get_locks(chat_id)
    res = ""
    locklist = []
    permslist = []
    if locks:
        res += "*" + "These are the current locks in this Chat:" + "*"
        if locks:
            locklist.append("sticker = `{}`".format(locks.sticker))
            locklist.append("audio = `{}`".format(locks.audio))
            locklist.append("voice = `{}`".format(locks.voice))
            locklist.append("document = `{}`".format(locks.document))
            locklist.append("video = `{}`".format(locks.video))
            locklist.append("contact = `{}`".format(locks.contact))
            locklist.append("photo = `{}`".format(locks.photo))
            locklist.append("gif = `{}`".format(locks.gif))
            locklist.append("url = `{}`".format(locks.url))
            locklist.append("bots = `{}`".format(locks.bots))
            locklist.append("forward = `{}`".format(locks.forward))
            locklist.append("game = `{}`".format(locks.game))
            locklist.append("location = `{}`".format(locks.location))
            locklist.append("rtl = `{}`".format(locks.rtl))
            locklist.append("button = `{}`".format(locks.button))
            locklist.append("egame = `{}`".format(locks.egame))
            locklist.append("phone = `{}`".format(locks.phone))
            locklist.append("command = `{}`".format(locks.command))
            locklist.append("email = `{}`".format(locks.email))
            locklist.append("anonchannel = `{}`".format(locks.anonchannel))
            locklist.append("forwardchannel = `{}`".format(locks.forwardchannel))
            locklist.append("forwardbot = `{}`".format(locks.forwardbot))
            locklist.append("videonote = `{}`".format(locks.videonote))
            locklist.append("emojicustom = `{}`".format(locks.emojicustom))
            locklist.append("stickerpremium = `{}`".format(locks.stickerpremium))
            locklist.append("stickeranimated = `{}`".format(locks.stickeranimated))

    permissions = await dispatcher.bot.get_chat(chat_id)
    if isinstance(permissions, Chat):
        permissions = permissions.permissions
        permslist.append("messages = `{}`".format(permissions.can_send_messages))
        permslist.append("media = `{}`".format(permissions.can_send_media_messages))
        permslist.append("poll = `{}`".format(permissions.can_send_polls))
        permslist.append("other = `{}`".format(permissions.can_send_other_messages))
        permslist.append(
            "previews = `{}`".format(permissions.can_add_web_page_previews)
        )
        permslist.append("info = `{}`".format(permissions.can_change_info))
        permslist.append("invite = `{}`".format(permissions.can_invite_users))
        permslist.append("pin = `{}`".format(permissions.can_pin_messages))
        permslist.append("topics = `{}`".format(permissions.can_manage_topics))

    if locklist:
        # Ordering lock list
        locklist.sort()
        # Building lock list string
        for x in locklist:
            res += "\n • {}".format(x)
    res += "\n\n*" + "These are the current chat permissions:" + "*"
    for x in permslist:
        res += "\n • {}".format(x)
    return res


@typing_action
@check_admin(is_user=True)
async def list_locks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user

    # Connection check
    conn = await connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = await dispatcher.bot.getChat(conn)
        chat_name = chat.title
    else:
        if update.effective_message.chat.type == "private":
            await send_message(
                update.effective_message,
                "This command is meant to use in group not in PM",
            )
            return ""
        chat = update.effective_chat
        chat_name = update.effective_message.chat.title

    res = await build_lock_message(chat.id)
    if conn:
        res = res.replace("Locks in", "*{}*".format(chat_name))

    await send_message(update.effective_message, res, parse_mode=ParseMode.MARKDOWN)


def get_permission_list(current, new):
    permissions = {
        "can_send_messages": None,
        "can_send_media_messages": None,
        "can_send_polls": None,
        "can_send_other_messages": None,
        "can_add_web_page_previews": None,
        "can_change_info": None,
        "can_invite_users": None,
        "can_pin_messages": None,
        "can_manage_topics": None,
    }
    permissions.update(current)
    permissions.update(new)
    new_permissions = ChatPermissions(**permissions)
    return new_permissions


async def __import_data__(chat_id, data, message):
    # set chat locks
    locks = data.get("locks", {})
    for itemlock in locks:
        if itemlock in LOCK_TYPES:
            sql.update_lock(chat_id, itemlock, locked=True)
        elif itemlock in LOCK_CHAT_RESTRICTION:
            sql.update_restriction(chat_id, itemlock, locked=True)
        else:
            pass


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


async def __chat_settings__(chat_id, user_id):
    return await build_lock_message(chat_id)


__help__ = """
➠ Do stickers annoy you? or want to avoid people sharing links? or pictures? \
You're in the right place!
The locks module allows you to lock away some common items in the \
telegram world; our bot will automatically delete them!

» /locktypes: Lists all possible locktypes

➠ *Admins only:*
» /lock <type>: Lock items of a certain type (not available in private)
» /unlock <type>: Unlock items of a certain type (not available in private)
» /locks: The current list of locks in this chat.

➠ Locks can be used to restrict a group's users.
eg:
Locking urls will auto-delete all messages with urls, locking stickers will restrict all \
non-admin users from sending stickers, etc.
Locking bots will stop non-admins from adding bots to the chat.
Locking anonchannel will stop anonymous channel from messaging in your group.

➠ *Note:*

» Unlocking permission *info* will allow members (non-admins) to change the group information, such as the description or the group name

» Unlocking permission *pin* will allow members (non-admins) to pin a message in a group
"""

__mod_name__ = "LOCKS"

LOCKTYPES_HANDLER = DisableAbleCommandHandler("locktypes", locktypes, block=False)
LOCK_HANDLER = CommandHandler(
    "lock", lock, block=False
)  # , filters=filters.ChatType.GROUPS)
UNLOCK_HANDLER = CommandHandler(
    "unlock", unlock, block=False
)  # , filters=filters.ChatType.GROUPS)
LOCKED_HANDLER = CommandHandler(
    "locks", list_locks, block=False
)  # , filters=filters.ChatType.GROUPS)

function(LOCK_HANDLER)
function(UNLOCK_HANDLER)
function(LOCKTYPES_HANDLER)
function(LOCKED_HANDLER)

function(
    MessageHandler(filters.ALL & filters.ChatType.GROUPS, del_lockables, block=False),
    PERM_GROUP,
)
