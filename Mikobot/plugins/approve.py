import html

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.error import BadRequest
from telegram.ext import CallbackQueryHandler, ContextTypes
from telegram.helpers import mention_html

import Database.sql.approve_sql as sql
from Mikobot import DRAGONS, dispatcher
from Mikobot.plugins.disable import DisableAbleCommandHandler
from Mikobot.plugins.helper_funcs.chat_status import check_admin
from Mikobot.plugins.helper_funcs.extraction import extract_user
from Mikobot.plugins.log_channel import loggable


@loggable
@check_admin(is_user=True)
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    args = context.args
    user = update.effective_user
    user_id = await extract_user(message, context, args)
    if not user_id:
        await message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user!",
        )
        return ""
    try:
        member = await chat.get_member(user_id)
    except BadRequest:
        return ""
    if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        await message.reply_text(
            "User is already admin - locks, blocklists, and antiflood already don't apply to them.",
        )
        return ""
    if sql.is_approved(message.chat_id, user_id):
        await message.reply_text(
            f"[{member.user.first_name}](tg://user?id={member.user.id}) is already approved in {chat_title}",
            parse_mode=ParseMode.MARKDOWN,
        )
        return ""
    sql.approve(message.chat_id, user_id)
    await message.reply_text(
        f"[{member.user.first_name}](tg://user?id={member.user.id}) has been approved in {chat_title}! They will now be ignored by automated admin actions like locks, blocklists, and antiflood.",
        parse_mode=ParseMode.MARKDOWN,
    )
    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#APPROVED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
    )

    return log_message


@loggable
@check_admin(is_user=True)
async def disapprove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    args = context.args
    user = update.effective_user
    user_id = await extract_user(message, context, args)
    if not user_id:
        await message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user!",
        )
        return ""
    try:
        member = await chat.get_member(user_id)
    except BadRequest:
        return ""
    if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        await message.reply_text("This user is an admin, they can't be unapproved.")
        return ""
    if not sql.is_approved(message.chat_id, user_id):
        await message.reply_text(f"{member.user.first_name} isn't approved yet!")
        return ""
    sql.disapprove(message.chat_id, user_id)
    await message.reply_text(
        f"{member.user.first_name} is no longer approved in {chat_title}.",
    )
    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNAPPROVED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
    )

    return log_message


@check_admin(is_user=True)
async def approved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    msg = "The following users are approved.\n"
    approved_users = sql.list_approved(message.chat_id)

    if not approved_users:
        await message.reply_text(f"No users are approved in {chat_title}.")
        return ""

    else:
        for i in approved_users:
            member = await chat.get_member(int(i.user_id))
            msg += f"- `{i.user_id}`: {member.user['first_name']}\n"

        await message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


@check_admin(is_user=True)
async def approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    user_id = await extract_user(message, context, args)

    if not user_id:
        await message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user!",
        )
        return ""
    member = await chat.get_member(int(user_id))
    if sql.is_approved(message.chat_id, user_id):
        await message.reply_text(
            f"{member.user['first_name']} is an approved user. Locks, antiflood, and blocklists won't apply to them.",
        )
    else:
        await message.reply_text(
            f"{member.user['first_name']} is not an approved user. They are affected by normal commands.",
        )


async def unapproveall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    member = await chat.get_member(user.id)

    approved_users = sql.list_approved(chat.id)
    if not approved_users:
        await update.effective_message.reply_text(
            f"No users are approved in {chat.title}."
        )
        return

    if member.status != ChatMemberStatus.OWNER and user.id not in DRAGONS:
        await update.effective_message.reply_text(
            "Only the chat owner can unapprove all users at once.",
        )
    else:
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Unapprove all users",
                        callback_data="unapproveall_user",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="Cancel",
                        callback_data="unapproveall_cancel",
                    ),
                ],
            ],
        )
        await update.effective_message.reply_text(
            f"Are you sure you would like to unapprove ALL users in {chat.title}? This action cannot be undone.",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN,
        )


async def unapproveall_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat = update.effective_chat
    message = update.effective_message
    member = await chat.get_member(query.from_user.id)
    if query.data == "unapproveall_user":
        if member.status == ChatMemberStatus.OWNER or query.from_user.id in DRAGONS:
            approved_users = sql.list_approved(chat.id)
            users = [int(i.user_id) for i in approved_users]
            for user_id in users:
                sql.disapprove(chat.id, user_id)
            await message.edit_text("Successfully Unapproved all user in this Chat.")
            return

        if member.status == "administrator":
            await query.answer("Only owner of the chat can do this.")

        if member.status == "member":
            await query.answer("You need to be admin to do this.")
    elif query.data == "unapproveall_cancel":
        if member.status == "creator" or query.from_user.id in DRAGONS:
            await message.edit_text(
                "Removing of all approved users has been cancelled."
            )
            return ""
        if member.status == "administrator":
            await query.answer("Only owner of the chat can do this.")
        if member.status == "member":
            await query.answer("You need to be admin to do this.")


__help__ = """
➠ Sometimes, you might trust a user not to send unwanted content.
Maybe not enough to make them admin, but you might be ok with locks, blacklists, and antiflood not applying to them.

➠ That's what approvals are for - approve of trustworthy users to allow them to send

➠ *Admin commands:*

» /approval: Check a user's approval status in this chat.

» /approve: Approve of a user. Locks, blacklists, and antiflood won't apply to them anymore.

» /unapprove: Unapprove of a user. They will now be subject to locks, blacklists, and antiflood again.

» /approved: List all approved users.

» /unapproveall: Unapprove *ALL* users in a chat. This cannot be undone.
"""

APPROVE = DisableAbleCommandHandler("approve", approve, block=False)
DISAPPROVE = DisableAbleCommandHandler("unapprove", disapprove, block=False)
APPROVED = DisableAbleCommandHandler("approved", approved, block=False)
APPROVAL = DisableAbleCommandHandler("approval", approval, block=False)
UNAPPROVEALL = DisableAbleCommandHandler("unapproveall", unapproveall, block=False)
UNAPPROVEALL_BTN = CallbackQueryHandler(
    unapproveall_btn, pattern=r"unapproveall_.*", block=False
)

dispatcher.add_handler(APPROVE)
dispatcher.add_handler(DISAPPROVE)
dispatcher.add_handler(APPROVED)
dispatcher.add_handler(APPROVAL)
dispatcher.add_handler(UNAPPROVEALL)
dispatcher.add_handler(UNAPPROVEALL_BTN)

__mod_name__ = "APPROVALS"
__command_list__ = ["approve", "unapprove", "approved", "approval"]
__handlers__ = [APPROVE, DISAPPROVE, APPROVED, APPROVAL]
