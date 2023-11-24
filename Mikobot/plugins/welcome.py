# <============================================== IMPORTS =========================================================>
import html
import os
import random
import re
import textwrap
import time
from contextlib import suppress
from datetime import datetime
from functools import partial

import unidecode
from PIL import Image, ImageChops, ImageDraw, ImageFont
from pyrogram import filters as ft
from pyrogram.types import ChatMemberUpdated, Message
from telegram import ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.helpers import escape_markdown, mention_html, mention_markdown

import Database.sql.welcome_sql as sql
from Database.mongodb.toggle_mongo import dwelcome_off, dwelcome_on, is_dwelcome_on
from Database.sql.global_bans_sql import is_user_gbanned
from Infamous.temp import temp
from Mikobot import DEV_USERS
from Mikobot import DEV_USERS as SUDO
from Mikobot import DRAGONS, EVENT_LOGS, LOGGER, OWNER_ID, app, dispatcher, function
from Mikobot.plugins.helper_funcs.chat_status import check_admin, is_user_ban_protected
from Mikobot.plugins.helper_funcs.misc import build_keyboard, revert_buttons
from Mikobot.plugins.helper_funcs.msg_types import get_welcome_type
from Mikobot.plugins.helper_funcs.string_handling import escape_invalid_curly_brackets
from Mikobot.plugins.log_channel import loggable
from Mikobot.utils.can_restrict import can_restrict

# <=======================================================================================================>

VALID_WELCOME_FORMATTERS = [
    "first",
    "last",
    "fullname",
    "username",
    "id",
    "count",
    "chatname",
    "mention",
]

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: dispatcher.bot.send_message,
    sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
    sql.Types.STICKER.value: dispatcher.bot.send_sticker,
    sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
    sql.Types.PHOTO.value: dispatcher.bot.send_photo,
    sql.Types.AUDIO.value: dispatcher.bot.send_audio,
    sql.Types.VOICE.value: dispatcher.bot.send_voice,
    sql.Types.VIDEO.value: dispatcher.bot.send_video,
}

VERIFIED_USER_WAITLIST = {}


# <================================================ TEMPLATE WELCOME FUNCTION =======================================================>
async def circle(pfp, size=(259, 259)):
    pfp = pfp.resize(size, Image.ANTIALIAS).convert("RGBA")
    bigsize = (pfp.size[0] * 3, pfp.size[1] * 3)
    mask = Image.new("L", bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(pfp.size, Image.ANTIALIAS)
    mask = ImageChops.darker(mask, pfp.split()[-1])
    pfp.putalpha(mask)
    return pfp


async def draw_multiple_line_text(image, text, font, text_start_height):
    draw = ImageDraw.Draw(image)
    image_width, image_height = image.size
    y_text = text_start_height
    lines = textwrap.wrap(text, width=50)
    for line in lines:
        line_width, line_height = font.getsize(line)
        draw.text(
            ((image_width - line_width) // 2, y_text), line, font=font, fill="black"
        )
        y_text += line_height


async def welcomepic(pic, user, chat, user_id):
    user = unidecode.unidecode(user)
    background = Image.open("Extra/bgg.jpg")
    background = background.resize(
        (background.size[0], background.size[1]), Image.ANTIALIAS
    )
    pfp = Image.open(pic).convert("RGBA")
    pfp = await circle(pfp, size=(259, 259))
    pfp_x = 55
    pfp_y = (background.size[1] - pfp.size[1]) // 2 + 38
    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype("Extra/Calistoga-Regular.ttf", 42)
    text_width, text_height = draw.textsize(f"{user} [{user_id}]", font=font)
    text_x = 20
    text_y = background.height - text_height - 20 - 25
    draw.text((text_x, text_y), f"{user} [{user_id}]", font=font, fill="white")
    background.paste(pfp, (pfp_x, pfp_y), pfp)
    welcome_image_path = f"downloads/welcome_{user_id}.png"
    background.save(welcome_image_path)
    return welcome_image_path


@app.on_chat_member_updated(ft.group)
async def member_has_joined(client, member: ChatMemberUpdated):
    if (
        not member.new_chat_member
        or member.new_chat_member.status in {"banned", "left", "restricted"}
        or member.old_chat_member
    ):
        return
    user = member.new_chat_member.user if member.new_chat_member else member.from_user
    if user.id in SUDO:
        await client.send_message(member.chat.id, "**Global Admins Joined The Chat!**")
        return
    elif user.is_bot:
        return
    else:
        chat_id = member.chat.id
        welcome_enabled = await is_dwelcome_on(chat_id)
        if not welcome_enabled:
            return
        if f"welcome-{chat_id}" in temp.MELCOW:
            try:
                await temp.MELCOW[f"welcome-{chat_id}"].delete()
            except:
                pass
        mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
        joined_date = datetime.fromtimestamp(time.time()).strftime("%Y.%m. %d %H:%M:%S")
        first_name = (
            f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
        )
        user_id = user.id
        dc = user.dc_id
        try:
            pic = await client.download_media(
                user.photo.big_file_id, file_name=f"pp{user_id}.png"
            )
        except AttributeError:
            pic = "Extra/profilepic.png"
        try:
            welcomeimg = await welcomepic(
                pic, user.first_name, member.chat.title, user_id
            )
            temp.MELCOW[f"welcome-{chat_id}"] = await client.send_photo(
                member.chat.id,
                photo=welcomeimg,
                caption=f"**𝗛𝗲𝘆❗️{mention}, 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝗧𝗼 {member.chat.title} 𝗚𝗿𝗼𝘂𝗽.**\n\n**➖➖➖➖➖➖➖➖➖➖➖➖**\n**𝗡𝗔𝗠𝗘 : {first_name}**\n**𝗜𝗗 : {user_id}**\n**𝗗𝗔𝗧𝗘 𝗝𝗢𝗜𝗡𝗘𝗗 : {joined_date}**",
            )
        except Exception as e:
            print(e)
        try:
            os.remove(f"downloads/welcome_{user_id}.png")
            os.remove(f"downloads/pp{user_id}.png")
        except Exception:
            pass


@app.on_message(ft.command("dwelcome on"))
@can_restrict
async def enable_welcome(_, message: Message):
    chat_id = message.chat.id
    welcome_enabled = await is_dwelcome_on(chat_id)
    if welcome_enabled:
        await message.reply_text("Default welcome is already enabled")
        return
    await dwelcome_on(chat_id)
    await message.reply_text("New default welcome message enabled for this chat.")


@app.on_message(ft.command("dwelcome off"))
@can_restrict
async def disable_welcome(_, message: Message):
    chat_id = message.chat.id
    welcome_enabled = await is_dwelcome_on(chat_id)
    if not welcome_enabled:
        await message.reply_text("Default welcome is already disabled")
        return
    await dwelcome_off(chat_id)
    await message.reply_text("New default welcome disabled for this chat.")


# <=======================================================================================================>


# <================================================ NORMAL WELCOME FUNCTION =======================================================>
async def send(update: Update, message, keyboard, backup_message):
    chat = update.effective_chat
    cleanserv = sql.clean_service(chat.id)
    reply = update.effective_message.message_id
    if cleanserv:
        try:
            await dispatcher.bot.delete_message(chat.id, update.message.message_id)
        except BadRequest:
            pass
        reply = False
    try:
        try:
            msg = await dispatcher.bot.send_message(
                chat.id,
                message,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        except:
            msg = await update.effective_message.reply_text(
                message,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                reply_to_message_id=reply,
            )
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            msg = await update.effective_message.reply_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard,
                quote=False,
            )
        elif excp.message == "Button_url_invalid":
            try:
                msg = await dispatcher.bot.send_message(
                    chat.id,
                    backup_message
                    + "\nNote: The current message has an invalid URL in one of its buttons. Please update.",
                    parse_mode=ParseMode.MARKDOWN,
                )
            except:
                msg = await update.effective_message.reply_text(
                    backup_message
                    + "\nNote: The current message has an invalid URL in one of its buttons. Please update.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_to_message_id=reply,
                )
        elif excp.message == "Unsupported URL protocol":
            try:
                msg = await dispatcher.bot.send_message(
                    chat.id,
                    backup_message
                    + "\nNote: The current message has buttons which use URL protocols that are unsupported by Telegram. Please update.",
                    parse_mode=ParseMode.MARKDOWN,
                )
            except:
                msg = await update.effective_message.reply_text(
                    backup_message
                    + "\nNote: The current message has buttons which use URL protocols that are unsupported by Telegram. Please update.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_to_message_id=reply,
                )
        elif excp.message == "Wrong URL host":
            try:
                msg = await dispatcher.bot.send_message(
                    chat.id,
                    backup_message
                    + "\nNote: The current message has some bad URLs. Please update.",
                    parse_mode=ParseMode.MARKDOWN,
                )
            except:
                msg = await update.effective_message.reply_text(
                    backup_message
                    + "\nNote: The current message has some bad URLs. Please update.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_to_message_id=reply,
                )
            LOGGER.warning(message)
            LOGGER.warning(keyboard)
            LOGGER.exception("Could not parse! Got invalid URL host errors")
        elif excp.message == "Have no rights to send a message":
            return
        else:
            try:
                msg = await dispatcher.bot.send_message(
                    chat.id,
                    backup_message
                    + "\nNote: An error occurred when sending the custom message. Please update.",
                    parse_mode=ParseMode.MARKDOWN,
                )
            except:
                msg = await update.effective_message.reply_text(
                    backup_message
                    + "\nNote: An error occurred when sending the custom message. Please update.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_to_message_id=reply,
                )
            LOGGER.exception()
    return msg


@loggable
async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot, job_queue = context.bot, context.job_queue
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    should_welc, cust_welcome, cust_content, welc_type = sql.get_welc_pref(chat.id)
    welc_mutes = sql.welcome_mutes(chat.id)
    human_checks = sql.get_human_checks(user.id, chat.id)

    new_members = update.effective_message.new_chat_members

    for new_mem in new_members:
        if new_mem.id == bot.id and not Mikobot.ALLOW_CHATS:
            with suppress(BadRequest):
                await update.effective_message.reply_text(
                    "Groups are disabled for {}, I'm outta here.".format(bot.first_name)
                )
            await bot.leave_chat(update.effective_chat.id)
            return

        welcome_log = None
        res = None
        sent = None
        should_mute = True
        welcome_bool = True
        media_wel = False

        if is_user_gbanned(new_mem.id):
            return

        if should_welc:
            reply = update.message.message_id
            cleanserv = sql.clean_service(chat.id)
            if cleanserv:
                try:
                    await dispatcher.bot.delete_message(
                        chat.id, update.message.message_id
                    )
                except BadRequest:
                    pass
                reply = False

            if new_mem.id == OWNER_ID:
                await update.effective_message.reply_text(
                    "Oh, darling, I have searched for you everywhere.",
                    reply_to_message_id=reply,
                )
                welcome_log = (
                    "{}\n"
                    "#USER_JOINED\n"
                    "Bot owner just joined the group".format(html.escape(chat.title))
                )
                continue

            elif new_mem.id in DEV_USERS:
                await update.effective_message.reply_text(
                    "Be cool! A member of the team just joined.",
                    reply_to_message_id=reply,
                )
                welcome_log = (
                    "{}\n"
                    "#USER_JOINED\n"
                    "Bot dev just joined the group".format(html.escape(chat.title))
                )
                continue

            elif new_mem.id in DRAGONS:
                await update.effective_message.reply_text(
                    "Whoa! A dragon disaster just joined! Stay alert!",
                    reply_to_message_id=reply,
                )
                welcome_log = (
                    "{}\n"
                    "#USER_JOINED\n"
                    "Bot sudo just joined the group".format(html.escape(chat.title))
                )
                continue

            elif new_mem.id == bot.id:
                creator = None
                for x in await bot.get_chat_administrators(update.effective_chat.id):
                    if x.status == "creator":
                        creator = x.user
                        break
                if creator:
                    reply = """#NEWGROUP \
                        \nID:   `{}` \
                    """.format(
                        chat.id
                    )

                    if chat.title:
                        reply += "\nGroup name:   **{}**".format(
                            escape_markdown(chat.title)
                        )

                    if chat.username:
                        reply += "\nUsername: @{}".format(
                            escape_markdown(chat.username)
                        )

                    reply += "\nCreator ID:   `{}`".format(creator.id)

                    if creator.username:
                        reply += "\nCreator Username: @{}".format(creator.username)

                    await bot.send_message(
                        EVENT_LOGS,
                        reply,
                        parse_mode="markdown",
                    )
                else:
                    await bot.send_message(
                        EVENT_LOGS,
                        "#NEW_GROUP\n<b>Group name:</b> {}\n<b>ID:</b> <code>{}</code>".format(
                            html.escape(chat.title),
                            chat.id,
                        ),
                        parse_mode=ParseMode.HTML,
                    )
                await update.effective_message.reply_text(
                    "I feel like I'm gonna suffocate in here.",
                    reply_to_message_id=reply,
                )
                continue

            else:
                buttons = sql.get_welc_buttons(chat.id)
                keyb = build_keyboard(buttons)

                if welc_type not in (sql.Types.TEXT, sql.Types.BUTTON_TEXT):
                    media_wel = True

                first_name = new_mem.first_name or "PersonWithNoName"

                if cust_welcome:
                    if cust_welcome == sql.DEFAULT_WELCOME:
                        cust_welcome = random.choice(
                            sql.DEFAULT_WELCOME_MESSAGES,
                        ).format(first=escape_markdown(first_name))

                    if new_mem.last_name:
                        fullname = escape_markdown(
                            "{} {}".format(first_name, new_mem.last_name)
                        )
                    else:
                        fullname = escape_markdown(first_name)
                    count = await chat.get_member_count()
                    mention = mention_markdown(new_mem.id, escape_markdown(first_name))
                    if new_mem.username:
                        username = "@{}".format(escape_markdown(new_mem.username))
                    else:
                        username = mention

                    valid_format = escape_invalid_curly_brackets(
                        cust_welcome,
                        VALID_WELCOME_FORMATTERS,
                    )
                    res = valid_format.format(
                        first=escape_markdown(first_name),
                        last=escape_markdown(new_mem.last_name or first_name),
                        fullname=escape_markdown(fullname),
                        username=username,
                        mention=mention,
                        count=count,
                        chatname=escape_markdown(chat.title),
                        id=new_mem.id,
                    )

                else:
                    res = random.choice(sql.DEFAULT_WELCOME_MESSAGES).format(
                        first=escape_markdown(first_name),
                    )
                    keyb = []

                backup_message = random.choice(sql.DEFAULT_WELCOME_MESSAGES).format(
                    first=escape_markdown(first_name),
                )
                keyboard = InlineKeyboardMarkup(keyb)

        else:
            welcome_bool = False
            res = None
            keyboard = None
            backup_message = None
            reply = None

        if (
            await is_user_ban_protected(
                chat, new_mem.id, await chat.get_member(new_mem.id)
            )
            or human_checks
        ):
            should_mute = False
        if new_mem.is_bot:
            should_mute = False

        if user.id == new_mem.id:
            if should_mute:
                if welc_mutes == "soft":
                    await bot.restrict_chat_member(
                        chat.id,
                        new_mem.id,
                        permissions=ChatPermissions(
                            can_send_messages=True,
                            can_send_media_messages=False,
                            can_send_other_messages=False,
                            can_invite_users=False,
                            can_pin_messages=False,
                            can_send_polls=False,
                            can_change_info=False,
                            can_add_web_page_previews=False,
                            can_manage_topics=False,
                        ),
                        until_date=(int(time.time() + 24 * 60 * 60)),
                    )
                if welc_mutes == "strong":
                    welcome_bool = False
                    if not media_wel:
                        VERIFIED_USER_WAITLIST.update(
                            {
                                new_mem.id: {
                                    "should_welc": should_welc,
                                    "media_wel": False,
                                    "status": False,
                                    "update": update,
                                    "res": res,
                                    "keyboard": keyboard,
                                    "backup_message": backup_message,
                                },
                            },
                        )
                    else:
                        VERIFIED_USER_WAITLIST.update(
                            {
                                new_mem.id: {
                                    "should_welc": should_welc,
                                    "chat_id": chat.id,
                                    "status": False,
                                    "media_wel": True,
                                    "cust_content": cust_content,
                                    "welc_type": welc_type,
                                    "res": res,
                                    "keyboard": keyboard,
                                },
                            },
                        )
                    new_join_mem = '<a href="tg://user?id={}">{}</a>'.format(
                        user.id, html.escape(new_mem.first_name)
                    )
                    message = await msg.reply_text(
                        "{}\nYou have 120 seconds to prove you're human.".format(
                            new_join_mem
                        ),
                        reply_markup=InlineKeyboardMarkup(
                            [
                                [
                                    InlineKeyboardButton(
                                        text="YES, I'M HUMAN",
                                        callback_data="user_join_({})".format(
                                            new_mem.id
                                        ),
                                    ),
                                ],
                            ],
                        ),
                        parse_mode=ParseMode.HTML,
                        reply_to_message_id=reply,
                    )
                    await bot.restrict_chat_member(
                        chat.id,
                        new_mem.id,
                        permissions=ChatPermissions(
                            can_send_messages=False,
                            can_invite_users=False,
                            can_pin_messages=False,
                            can_send_polls=False,
                            can_change_info=False,
                            can_send_media_messages=False,
                            can_send_other_messages=False,
                            can_add_web_page_previews=False,
                            can_manage_topics=False,
                        ),
                    )
                    job_queue.run_once(
                        partial(check_not_bot, new_mem, chat.id, message.message_id),
                        120,
                        name="welcomemute",
                    )

        if welcome_bool:
            if media_wel:
                sent = await ENUM_FUNC_MAP[welc_type](
                    chat.id,
                    cust_content,
                    caption=res,
                    reply_markup=keyboard,
                    reply_to_message_id=reply,
                    parse_mode="markdown",
                )
            else:
                sent = await send(update, res, keyboard, backup_message)
            prev_welc = sql.get_clean_pref(chat.id)
            if prev_welc:
                try:
                    await bot.delete_message(chat.id, prev_welc)
                except BadRequest:
                    pass

                if sent:
                    sql.set_clean_welcome(chat.id, sent.message_id)

        if welcome_log:
            return welcome_log

        if user.id == new_mem.id:
            welcome_log = (
                "{}\n"
                "#USER_JOINED\n"
                "<b>User</b>: {}\n"
                "<b>ID</b>: <code>{}</code>".format(
                    html.escape(chat.title),
                    mention_html(user.id, user.first_name),
                    user.id,
                )
            )
        elif new_mem.is_bot and user.id != new_mem.id:
            welcome_log = (
                "{}\n"
                "#BOT_ADDED\n"
                "<b>Bot</b>: {}\n"
                "<b>ID</b>: <code>{}</code>".format(
                    html.escape(chat.title),
                    mention_html(new_mem.id, new_mem.first_name),
                    new_mem.id,
                )
            )
        else:
            welcome_log = (
                "{}\n"
                "#USER_ADDED\n"
                "<b>User</b>: {}\n"
                "<b>ID</b>: <code>{}</code>".format(
                    html.escape(chat.title),
                    mention_html(new_mem.id, new_mem.first_name),
                    new_mem.id,
                )
            )
        return welcome_log

    return ""


async def check_not_bot(member, chat_id, message_id, context):
    bot = context.bot
    member_dict = VERIFIED_USER_WAITLIST.pop(member.id)
    member_status = member_dict.get("status")
    if not member_status:
        try:
            await bot.unban_chat_member(chat_id, member.id)
        except:
            pass

        try:
            await bot.edit_message_text(
                "Kicks user\nThey can always rejoin and try.",
                chat_id=chat_id,
                message_id=message_id,
            )
        except:
            pass


async def left_member(update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    chat = update.effective_chat
    user = update.effective_user
    should_goodbye, cust_goodbye, goodbye_type = sql.get_gdbye_pref(chat.id)

    if user.id == bot.id:
        return

    if should_goodbye:
        reply = update.message.message_id
        cleanserv = sql.clean_service(chat.id)
        if cleanserv:
            try:
                await dispatcher.bot.delete_message(chat.id, update.message.message_id)
            except BadRequest:
                pass
            reply = False

        left_mem = update.effective_message.left_chat_member
        if left_mem:
            if is_user_gbanned(left_mem.id):
                return

            if left_mem.id == bot.id:
                return

            if left_mem.id == OWNER_ID:
                await update.effective_message.reply_text(
                    "My master left..",
                    reply_to_message_id=reply,
                )
                return

            elif left_mem.id in DEV_USERS:
                await update.effective_message.reply_text(
                    "see you later pro!",
                    reply_to_message_id=reply,
                )
                return

            if goodbye_type != sql.Types.TEXT and goodbye_type != sql.Types.BUTTON_TEXT:
                await ENUM_FUNC_MAP[goodbye_type](chat.id, cust_goodbye)
                return

            first_name = left_mem.first_name or "PersonWithNoName"
            if cust_goodbye:
                if cust_goodbye == sql.DEFAULT_GOODBYE:
                    cust_goodbye = random.choice(sql.DEFAULT_GOODBYE_MESSAGES).format(
                        first=first_name,
                    )
                if left_mem.last_name:
                    fullname = "{} {}".format(first_name, left_mem.last_name)
                else:
                    fullname = first_name
                count = await chat.get_member_count()
                mention = mention_markdown(left_mem.id, first_name)
                if left_mem.username:
                    username = "@{}".format(left_mem.username)
                else:
                    username = mention

                valid_format = escape_invalid_curly_brackets(
                    cust_goodbye,
                    VALID_WELCOME_FORMATTERS,
                )
                res = valid_format.format(
                    first=first_name,
                    last=left_mem.last_name or first_name,
                    fullname=fullname,
                    username=username,
                    mention=mention,
                    count=count,
                    chatname=chat.title,
                    id=left_mem.id,
                )
                buttons = sql.get_gdbye_buttons(chat.id)
                keyb = build_keyboard(buttons)

            else:
                res = random.choice(sql.DEFAULT_GOODBYE_MESSAGES).format(
                    first=first_name,
                )
                keyb = []

            keyboard = InlineKeyboardMarkup(keyb)

            await send(
                update,
                res,
                keyboard,
                random.choice(sql.DEFAULT_GOODBYE_MESSAGES).format(first=first_name),
            )


@check_admin(is_user=True)
async def welcome(update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    chat = update.effective_chat
    if not args or args[0].lower() == "noformat":
        noformat = True
        pref, welcome_m, cust_content, welcome_type = sql.get_welc_pref(chat.id)
        await update.effective_message.reply_text(
            f"This chat has its welcome setting set to: `{pref}`.\n"
            f"The welcome message (not filling the {{}}) is:",
            parse_mode=ParseMode.MARKDOWN,
        )

        if welcome_type == sql.Types.BUTTON_TEXT or welcome_type == sql.Types.TEXT:
            buttons = sql.get_welc_buttons(chat.id)
            if noformat:
                welcome_m += revert_buttons(buttons)
                await update.effective_message.reply_text(welcome_m)
            else:
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)
                await send(update, welcome_m, keyboard, sql.DEFAULT_WELCOME)
        else:
            buttons = sql.get_welc_buttons(chat.id)
            if noformat:
                welcome_m += revert_buttons(buttons)
                await ENUM_FUNC_MAP[welcome_type](
                    chat.id, cust_content, caption=welcome_m
                )
            else:
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)
                ENUM_FUNC_MAP[welcome_type](
                    chat.id,
                    cust_content,
                    caption=welcome_m,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )

    elif len(args) >= 1:
        if args[0].lower() in ("on", "yes"):
            sql.set_welc_preference(str(chat.id), True)
            await update.effective_message.reply_text(
                "Okay! I'll greet members when they join.",
            )

        elif args[0].lower() in ("off", "no"):
            sql.set_welc_preference(str(chat.id), False)
            await update.effective_message.reply_text(
                "I'll go loaf around and not welcome anyone then.",
            )

        else:
            await update.effective_message.reply_text(
                "I understand 'on/yes' or 'off/no' only!",
            )


@check_admin(is_user=True)
async def goodbye(update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    chat = update.effective_chat

    if not args or args[0] == "noformat":
        noformat = True
        pref, goodbye_m, goodbye_type = sql.get_gdbye_pref(chat.id)
        await update.effective_message.reply_text(
            f"This chat has its goodbye setting set to: `{pref}`.\n"
            f"The goodbye message (not filling the {{}}) is:",
            parse_mode=ParseMode.MARKDOWN,
        )

        if goodbye_type == sql.Types.BUTTON_TEXT:
            buttons = sql.get_gdbye_buttons(chat.id)
            if noformat:
                goodbye_m += revert_buttons(buttons)
                await update.effective_message.reply_text(goodbye_m)

            else:
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)
                await send(update, goodbye_m, keyboard, sql.DEFAULT_GOODBYE)

        else:
            if noformat:
                await ENUM_FUNC_MAP[goodbye_type](chat.id, goodbye_m)

            else:
                await ENUM_FUNC_MAP[goodbye_type](
                    chat.id, goodbye_m, parse_mode=ParseMode.MARKDOWN
                )

    elif len(args) >= 1:
        if args[0].lower() in ("on", "yes"):
            sql.set_gdbye_preference(str(chat.id), True)
            await update.effective_message.reply_text("Okay its set to on!")

        elif args[0].lower() in ("off", "no"):
            sql.set_gdbye_preference(str(chat.id), False)
            await update.effective_message.reply_text("Okay its set to no!")

        else:
            await update.effective_message.reply_text(
                "I understand 'on/yes' or 'off/no' only!",
            )


@check_admin(is_user=True)
@loggable
async def set_welcome(update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    text, data_type, content, buttons = get_welcome_type(msg)

    if data_type is None:
        await msg.reply_text("You didn't specify what to reply with!")
        return ""

    sql.set_custom_welcome(chat.id, content, text, data_type, buttons)
    await msg.reply_text("Successfully set custom welcome message!")

    return (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#SET_WELCOME\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        "Set the welcome message."
    )


@check_admin(is_user=True)
@loggable
async def reset_welcome(update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    sql.set_custom_welcome(chat.id, None, sql.DEFAULT_WELCOME, sql.Types.TEXT)
    await update.effective_message.reply_text(
        "Successfully reset welcome message to default!"
    )

    return (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#RESET_WELCOME\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        "Reset the welcome message to default."
    )


@check_admin(is_user=True)
@loggable
async def set_goodbye(update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    text, data_type, content, buttons = get_welcome_type(msg)

    if data_type is None:
        await msg.reply_text("You didn't specify what to reply with!")
        return ""

    sql.set_custom_gdbye(chat.id, content or text, data_type, buttons)
    await msg.reply_text("Successfully set custom goodbye message!")
    return (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#SET_GOODBYE\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        "Set the goodbye message."
    )


@check_admin(is_user=True)
@loggable
async def reset_goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    chat = update.effective_chat
    user = update.effective_user

    sql.set_custom_gdbye(chat.id, sql.DEFAULT_GOODBYE, sql.Types.TEXT)
    await update.effective_message.reply_text(
        "Successfully reset goodbye message to default!",
    )

    return (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#RESET_GOODBYE\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"Reset the goodbye message."
    )


@check_admin(is_user=True)
@loggable
async def welcomemute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if len(args) >= 1:
        if args[0].lower() in ("off", "no"):
            sql.set_welcome_mutes(chat.id, False)
            await msg.reply_text("I will no longer mute people on joining!")
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#WELCOME_MUTE\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"Has toggled welcome mute to <b>off</b>."
            )
        elif args[0].lower() in ["soft"]:
            sql.set_welcome_mutes(chat.id, "soft")
            await msg.reply_text(
                "I will restrict users permission to send media for 24 hours.",
            )
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#𝐖𝐄𝐋𝐂𝐎𝐌𝐄_𝐌𝐔𝐓𝐄\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"Has toggled welcome mute to <b>soft</b>."
            )
        elif args[0].lower() in ["strong"]:
            sql.set_welcome_mutes(chat.id, "strong")
            await msg.reply_text(
                "I will now mute people when they join until they prove they're not a bot. They will have 120 seconds before they get kicked.",
            )
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#𝐖𝐄𝐋𝐂𝐎𝐌𝐄_𝐌𝐔𝐓𝐄\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"Has toggled welcome mute to <b>strong</b>."
            )
        else:
            await msg.reply_text(
                "Please enter <code>off</code>/<code>no</code>/<code>soft</code>/<code>strong</code>!",
                parse_mode=ParseMode.HTML,
            )
            return ""
    else:
        curr_setting = sql.welcome_mutes(chat.id)
        reply = (
            "Give me a setting!\nChoose one out of: <code>off</code>/<code>no</code> or <code>soft</code> or <code>strong</code> only! \n"
            f"Current setting: <code>{curr_setting}</code>"
        )
        await msg.reply_text(reply, parse_mode=ParseMode.HTML)
        return ""


@check_admin(is_user=True)
@loggable
async def clean_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    args = context.args
    chat = update.effective_chat
    user = update.effective_user

    if not args:
        clean_pref = sql.get_clean_pref(chat.id)
        if clean_pref:
            await update.effective_message.reply_text(
                "I should be deleting welcome messages up to two days old.",
            )
        else:
            await update.effective_message.reply_text(
                "I'm currently not deleting old welcome messages!",
            )
        return ""

    if args[0].lower() in ("on", "yes"):
        sql.set_clean_welcome(str(chat.id), True)
        await update.effective_message.reply_text(
            "I'll try to delete old welcome messages!"
        )
        return (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#𝐂𝐋𝐄𝐀𝐍_𝐖𝐄𝐋𝐂𝐎𝐌𝐄\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            "Has toggled clean welcomes to <code>on</code>."
        )
    elif args[0].lower() in ("off", "no"):
        sql.set_clean_welcome(str(chat.id), False)
        await update.effective_message.reply_text(
            "I won't delete old welcome messages."
        )
        return (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#𝐂𝐋𝐄𝐀𝐍_𝐖𝐄𝐋𝐂𝐎𝐌𝐄\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            "Has toggled clean welcomes to <code>off</code>."
        )
    else:
        await update.effective_message.reply_text(
            "I understand 'on/yes' or 'off/no' only!",
        )
        return ""


@check_admin(is_user=True)
async def cleanservice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    if chat.type != chat.PRIVATE:
        if len(args) >= 1:
            var = args[0]
            if var in ("no", "off"):
                sql.set_clean_service(chat.id, False)
                await update.effective_message.reply_text(
                    "Welcome clean service is : off"
                )
            elif var in ("yes", "on"):
                sql.set_clean_service(chat.id, True)
                await update.effective_message.reply_text(
                    "Welcome clean service is : on"
                )
            else:
                await update.effective_message.reply_text(
                    "Invalid option",
                    parse_mode=ParseMode.HTML,
                )
        else:
            await update.effective_message.reply_text(
                "Usage is <code>on</code>/<code>yes</code> or <code>off</code>/<code>no</code>",
                parse_mode=ParseMode.HTML,
            )
    else:
        curr = sql.clean_service(chat.id)
        if curr:
            await update.effective_message.reply_text(
                "Welcome clean service is : <code>on</code>",
                parse_mode=ParseMode.HTML,
            )
        else:
            await update.effective_message.reply_text(
                "Welcome clean service is : <code>off</code>",
                parse_mode=ParseMode.HTML,
            )


async def user_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    query = update.callback_query
    bot = context.bot
    match = re.match(r"user_join_\((.+?)\)", query.data)
    message = update.effective_message
    join_user = int(match.group(1))

    if join_user == user.id:
        sql.set_human_checks(user.id, chat.id)
        member_dict = VERIFIED_USER_WAITLIST.pop(user.id)
        member_dict["status"] = True
        VERIFIED_USER_WAITLIST.update({user.id: member_dict})
        await query.answer(text="Yeet! You're a human, unmuted!")
        await bot.restrict_chat_member(
            chat.id,
            user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_send_polls=True,
                can_change_info=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_manage_topics=False,
            ),
        )
        try:
            await bot.deleteMessage(chat.id, message.message_id)
        except:
            pass
        if member_dict["should_welc"]:
            if member_dict["media_wel"]:
                # topic_chat = get_action_topic(chat.id)
                sent = await ENUM_FUNC_MAP[member_dict["welc_type"]](
                    member_dict["chat_id"],
                    member_dict["cust_content"],
                    caption=member_dict["res"],
                    reply_markup=member_dict["keyboard"],
                    parse_mode="markdown",
                )
            else:
                sent = await send(
                    member_dict["update"],
                    member_dict["res"],
                    member_dict["keyboard"],
                    member_dict["backup_message"],
                )

            prev_welc = sql.get_clean_pref(chat.id)
            if prev_welc:
                try:
                    await bot.delete_message(chat.id, prev_welc)
                except BadRequest:
                    pass

                if sent:
                    sql.set_clean_welcome(chat.id, sent.message_id)

    else:
        await query.answer(text="You're not allowed to do this!")


WELC_MUTE_HELP_TXT = (
    "You can get the bot to mute new people who join your group and hence prevent spambots from flooding your group. "
    "The following options are possible:\n"
    "• `/welcomemute soft`: Restricts new members from sending media for 24 hours.\n"
    "• `/welcomemute strong`: Mutes new members until they tap on a button, thereby verifying they're human.\n"
    "• `/welcomemute off`: Turns off welcomemute.\n"
    "Note: Strong mode kicks a user from the chat if they don't verify in 120 seconds. They can always rejoin though."
)


@check_admin(is_user=True)
async def welcome_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    WELC_HELP_TXT = (
        "Your group's welcome/goodbye messages can be personalized in multiple ways. If you want the messages"
        " to be individually generated, like the default welcome message is, you can use these variables:\n"
        " • `{first}`: This represents the user's *first* name\n"
        " • `{last}`: This represents the user's *last* name. Defaults to *first name* if the user has no last name.\n"
        " • `{fullname}`: This represents the user's *full* name. Defaults to *first name* if the user has no last name.\n"
        " • `{username}`: This represents the user's *username*. Defaults to a *mention* of the user's"
        " first name if they have no username.\n"
        " • `{mention}`: This simply *mentions* a user - tagging them with their first name.\n"
        " • `{id}`: This represents the user's *ID*\n"
        " • `{count}`: This represents the user's *member number*.\n"
        " • `{chatname}`: This represents the *current chat name*.\n"
        "\nEach variable must be surrounded by `{}` to be replaced.\n"
        "Welcome messages also support markdown, so you can make any elements bold/italic/code/links. "
        "Buttons are also supported, so you can make your welcomes look awesome with some nice intro buttons."
        "\nTo create a button linking to your rules, use this: `[rules](buttonurl://t.me/"
        f"{context.bot.username}?start=group_id)`. Simply replace `group_id` with your group's ID,"
        " which can be obtained via /id, and you're good to go. Note that group IDs are usually preceded by a `-` sign, so please don't remove it."
        " You can even set images/gifs/videos/voice messages as the welcome message by replying to the desired media,"
        " and calling `/setwelcome`."
    )

    await update.effective_message.reply_text(
        WELC_HELP_TXT, parse_mode=ParseMode.MARKDOWN
    )


@check_admin(is_user=True)
async def welcome_mute_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        WELC_MUTE_HELP_TXT,
        parse_mode=ParseMode.MARKDOWN,
    )


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    welcome_pref = sql.get_welc_pref(chat_id)[0]
    goodbye_pref = sql.get_gdbye_pref(chat_id)[0]
    return (
        f"This chat has its welcome preference set to `{welcome_pref}`.\n"
        f"Its goodbye preference is `{goodbye_pref}`."
    )


# <=================================================== HELP ====================================================>


__help__ = """
➠ *Admins Only:*

➠ *Default Welcome CMDS:*
» /dwelcome on : Enables the default template welcome.
» /dwelcome off : Disables the default template welcome.

➠ *Normal Welcome CMDS:*
» /welcome <on/off>: Enable/disable welcome messages.
» /welcome: Shows current welcome settings.
» /welcome noformat: Shows current welcome settings, without the formatting - useful to recycle your welcome messages!
» /goodbye: Same usage and args as /welcome
» /setwelcome <sometext>: Set a custom welcome message. If used replying to media, uses that media.
» /setgoodbye <sometext>: Set a custom goodbye message. If used replying to media, uses that media.
» /resetwelcome: Reset to the default welcome message.
» /resetgoodbye: Reset to the default goodbye message.
» /cleanwelcome <on/off>: On new member, try to delete the previous welcome message to avoid spamming the chat.
» /welcomemutehelp: Gives information about welcome mutes.
» /cleanservice <on/off>: Deletes Telegram's welcome/left service messages.

➠ *Example:*
User joined chat, user left chat.

➠ *Welcome Markdown:*
» /welcomehelp: View more formatting information for custom welcome/goodbye messages.
"""

# <================================================ HANDLER =======================================================>
NEW_MEM_HANDLER = MessageHandler(
    filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member, block=False
)
LEFT_MEM_HANDLER = MessageHandler(
    filters.StatusUpdate.LEFT_CHAT_MEMBER, left_member, block=False
)
WELC_PREF_HANDLER = CommandHandler(
    "welcome", welcome, filters=filters.ChatType.GROUPS, block=False
)
GOODBYE_PREF_HANDLER = CommandHandler(
    "goodbye", goodbye, filters=filters.ChatType.GROUPS, block=False
)
SET_WELCOME = CommandHandler(
    "setwelcome", set_welcome, filters=filters.ChatType.GROUPS, block=False
)
SET_GOODBYE = CommandHandler(
    "setgoodbye", set_goodbye, filters=filters.ChatType.GROUPS, block=False
)
RESET_WELCOME = CommandHandler(
    "resetwelcome", reset_welcome, filters=filters.ChatType.GROUPS, block=False
)
RESET_GOODBYE = CommandHandler(
    "resetgoodbye", reset_goodbye, filters=filters.ChatType.GROUPS, block=False
)
WELCOMEMUTE_HANDLER = CommandHandler(
    "welcomemute", welcomemute, filters=filters.ChatType.GROUPS, block=False
)
CLEAN_SERVICE_HANDLER = CommandHandler(
    "cleanservice", cleanservice, filters=filters.ChatType.GROUPS, block=False
)
CLEAN_WELCOME = CommandHandler(
    "cleanwelcome", clean_welcome, filters=filters.ChatType.GROUPS, block=False
)
WELCOME_HELP = CommandHandler("welcomehelp", welcome_help, block=False)
WELCOME_MUTE_HELP = CommandHandler("welcomemutehelp", welcome_mute_help, block=False)
BUTTON_VERIFY_HANDLER = CallbackQueryHandler(
    user_button, pattern=r"user_join_", block=False
)

function(NEW_MEM_HANDLER)
function(LEFT_MEM_HANDLER)
function(WELC_PREF_HANDLER)
function(GOODBYE_PREF_HANDLER)
function(SET_WELCOME)
function(SET_GOODBYE)
function(RESET_WELCOME)
function(RESET_GOODBYE)
function(CLEAN_WELCOME)
function(WELCOME_HELP)
function(WELCOMEMUTE_HANDLER)
function(CLEAN_SERVICE_HANDLER)
function(BUTTON_VERIFY_HANDLER)
function(WELCOME_MUTE_HELP)

__mod_name__ = "WELCOME"
__command_list__ = []
__handlers__ = [
    NEW_MEM_HANDLER,
    LEFT_MEM_HANDLER,
    WELC_PREF_HANDLER,
    GOODBYE_PREF_HANDLER,
    SET_WELCOME,
    SET_GOODBYE,
    RESET_WELCOME,
    RESET_GOODBYE,
    CLEAN_WELCOME,
    WELCOME_HELP,
    WELCOMEMUTE_HANDLER,
    CLEAN_SERVICE_HANDLER,
    BUTTON_VERIFY_HANDLER,
    WELCOME_MUTE_HELP,
]
# <================================================ END =======================================================>
