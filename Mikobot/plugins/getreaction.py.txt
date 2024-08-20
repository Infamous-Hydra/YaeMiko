from pyrogram import filters
from pyrogram.types import Message

from Mikobot import app


def has_reactions(_, __, m: Message):
    return bool(m.reply_to_message.reactions)


@app.on_message(filters.command("getreaction") & filters.reply)
def get_reaction_list(client, message):
    reaction_list = {}
    reply_to_message = message.reply_to_message
    for reaction in reply_to_message.reactions:
        users = []
        for user_id in reaction.user_ids:
            user = client.get_users(user_id)
            users.append(user.username or user.first_name)
        reaction_list[reaction.name] = users

    if reaction_list:
        result_text = "\n".join(
            f"{reaction}: {', '.join(users)}"
            for reaction, users in reaction_list.items()
        )
        message.reply_text(result_text)
    else:
        message.reply_text("No reactions found in the replied message.")


@app.on_message(filters.text & filters.reply & filters.create(has_reactions))
def reply_get_reaction_list(client, message):
    if message.text.lower() == "/getreaction":
        get_reaction_list(client, message)
