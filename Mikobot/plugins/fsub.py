# <============================================== IMPORTS =========================================================>
from telethon import Button, events, types
from telethon.errors import ChatAdminRequiredError, UserNotParticipantError
from telethon.tl.functions.channels import GetParticipantRequest

from Database.mongodb import fsub_db as db
from Mikobot import BOT_ID
from Mikobot import DRAGONS as DEVS
from Mikobot import OWNER_ID, tbot
from Mikobot.events import register

# <=======================================================================================================>

# Constants
F_SUBSCRIBE_COMMAND = "/(fsub|Fsub|forcesubscribe|Forcesub|forcesub|Forcesubscribe)"
FORCESUBSCRIBE_ON = ["on", "yes", "y"]
FORCESUBSCRIBE_OFF = ["off", "no", "n"]


# <================================================ FUNCTION =======================================================>
def fsk_ck(**args):
    def decorator(func):
        tbot.add_event_handler(func, events.CallbackQuery(**args))
        return func

    return decorator


# Helper functions
async def is_admin(chat_id, user_id):
    try:
        p = await tbot(GetParticipantRequest(chat_id, user_id))
    except UserNotParticipantError:
        return False
    return isinstance(
        p.participant, (types.ChannelParticipantAdmin, types.ChannelParticipantCreator)
    )


async def participant_check(channel, user_id):
    try:
        await tbot(GetParticipantRequest(channel, int(user_id)))
        return True
    except UserNotParticipantError:
        return False
    except Exception:
        return False


# Main command function
@register(pattern=f"^{F_SUBSCRIBE_COMMAND} ?(.*)")
async def force_subscribe(event):
    """Handle the force subscribe command."""
    if event.is_private:
        return

    if event.is_group:
        perm = await event.client.get_permissions(event.chat_id, event.sender_id)
        if not perm.is_admin:
            return await event.reply("You need to be an admin to do this.")

        if not perm.is_creator:
            return await event.reply(
                "❗ Group creator required\nYou have to be the group creator to do that."
            )

    try:
        channel = event.text.split(None, 1)[1]
    except IndexError:
        channel = None

    if not channel:
        chat_db = db.fs_settings(event.chat_id)
        if not chat_db:
            await event.reply("Force subscribe is disabled in this chat.")
        else:
            await event.reply(
                f"Force subscribe is currently enabled. Users are forced to join @{chat_db.channel} to speak here."
            )
    elif channel.lower() in FORCESUBSCRIBE_ON:
        await event.reply("Please specify the channel username.")
    elif channel.lower() in FORCESUBSCRIBE_OFF:
        await event.reply("**Force subscribe is disabled successfully.**")
        db.disapprove(event.chat_id)
    else:
        try:
            channel_entity = await event.client.get_entity(channel)
        except:
            return await event.reply("Invalid channel username provided.")

        channel = channel_entity.username
        try:
            if not channel_entity.broadcast:
                return await event.reply("That's not a valid channel.")
        except:
            return await event.reply("That's not a valid channel.")

        if not await participant_check(channel, BOT_ID):
            return await event.reply(
                f"**Not an admin in the channel**\nI am not an admin in the [channel](https://t.me/{channel}). Add me as an admin to enable force subscribe.",
                link_preview=False,
            )

        db.add_channel(event.chat_id, str(channel))
        await event.reply(f"Force subscribe is enabled to @{channel}.")


# Event handler for new messages
@tbot.on(events.NewMessage())
async def force_subscribe_new_message(e):
    """Handle new messages for force subscribe."""
    if not db.fs_settings(e.chat_id):
        return

    if e.is_private or not e.from_id or e.sender_id in DEVS or e.sender_id == OWNER_ID:
        return

    if not e.chat.admin_rights or not e.chat.admin_rights.ban_users:
        return

    try:
        channel = db.fs_settings(e.chat_id)["channel"]
        check = await participant_check(channel, e.sender_id)
    except (ChatAdminRequiredError, UserNotParticipantError):
        return

    if not check:
        buttons = [
            Button.url("Join Channel", f"t.me/{channel}"),
            Button.inline("Unmute Me", data=f"fs_{e.sender_id}"),
        ]

        txt = f'<b><a href="tg://user?id={e.sender_id}">{e.sender.first_name}</a></b>, you have <b>not subscribed</b> to our <b><a href="t.me/{channel}">channel</a></b> yet. Please <b><a href="t.me/{channel}">join</a></b> and press the button below to unmute yourself.'
        await e.reply(txt, buttons=buttons, parse_mode="html", link_preview=False)
        await e.client.edit_permissions(e.chat_id, e.sender_id, send_messages=False)


# Inline query handler
@fsk_ck(pattern=r"fs(\_(.*))")
async def unmute_force_subscribe(event):
    """Handle inline query for unmuting force subscribe."""
    user_id = int(((event.pattern_match.group(1)).decode()).split("_", 1)[1])

    if not event.sender_id == user_id:
        return await event.answer("This is not meant for you.", alert=True)

    channel = db.fs_settings(event.chat_id)["channel"]
    try:
        check = await participant_check(channel, user_id)
    except ChatAdminRequiredError:
        check = False
        return

    if not check:
        return await event.answer(
            "You have to join the channel first, to get unmuted!", alert=True
        )

    try:
        await event.client.edit_permissions(event.chat_id, user_id, send_messages=True)
    except ChatAdminRequiredError:
        pass

    await event.delete()


# <=================================================== HELP ====================================================>


__help__ = """
➠ *Dazai has the capability to hush members who haven't yet subscribed to your channel until they decide to hit that subscribe button.*
➠ *When activated, I'll silence those who are not subscribed and provide them with an option to unmute. Once they click the button, I'll lift the mute.*

➠ Configuration Process
➠ Exclusively for Creators
➠ Grant me admin privileges in your group
➠ Designate me as an admin in your channel

➠ *Commands*
» /fsub channel\_username - to initiate and customize settings for the channel.

➠ *Kick things off with...*
» /fsub - to review the current settings.
» /fsub off - to deactivate the force subscription feature.

➠ *If you disable fsub, you'll need to set it up again for it to take effect. Utilize /fsub channel\_username.*
"""
__mod_name__ = "F-SUB"
# <================================================ END =======================================================>
