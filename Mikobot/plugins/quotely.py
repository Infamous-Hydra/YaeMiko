# <============================================== IMPORTS =========================================================>
import base64
import os
from random import choice

from aiohttp import ContentTypeError
from PIL import Image
from telethon.tl import types
from telethon.utils import get_display_name, get_peer_id

from Mikobot import DEV_USERS
from Mikobot.events import register

# <=======================================================================================================>


# <================================================ CLASS & FUNCTION =======================================================>
class Quotly:
    _API = "https://bot.lyo.su/quote/generate"
    _entities = {
        types.MessageEntityPhone: "phone_number",
        types.MessageEntityMention: "mention",
        types.MessageEntityBold: "bold",
        types.MessageEntityCashtag: "cashtag",
        types.MessageEntityStrike: "strikethrough",
        types.MessageEntityHashtag: "hashtag",
        types.MessageEntityEmail: "email",
        types.MessageEntityMentionName: "text_mention",
        types.MessageEntityUnderline: "underline",
        types.MessageEntityUrl: "url",
        types.MessageEntityTextUrl: "text_link",
        types.MessageEntityBotCommand: "bot_command",
        types.MessageEntityCode: "code",
        types.MessageEntityPre: "pre",
    }

    async def _format_quote(self, event, reply=None, sender=None, type_="private"):
        async def telegraph(file_):
            file = file_ + ".png"
            Image.open(file_).save(file, "PNG")
            files = {"file": open(file, "rb").read()}
            uri = (
                "https://telegra.ph"
                + (
                    await async_searcher(
                        "https://telegra.ph/upload", post=True, data=files, re_json=True
                    )
                )[0]["src"]
            )
            os.remove(file)
            os.remove(file_)
            return uri

        reply = (
            {
                "name": get_display_name(reply.sender) or "Deleted Account",
                "text": reply.raw_text,
                "chatId": reply.chat_id,
            }
            if reply
            else {}
        )

        is_fwd = event.fwd_from
        name, last_name = None, None

        if sender and sender.id not in DEV_USERS:
            id_ = get_peer_id(sender)
            name = get_display_name(sender)
        elif not is_fwd:
            id_ = event.sender_id
            sender = await event.get_sender()
            name = get_display_name(sender)
        else:
            id_, sender = None, None
            name = is_fwd.from_name
            if is_fwd.from_id:
                id_ = get_peer_id(is_fwd.from_id)
                try:
                    sender = await event.client.get_entity(id_)
                    name = get_display_name(sender)
                except ValueError:
                    pass
        if sender and hasattr(sender, "last_name"):
            last_name = sender.last_name

        entities = (
            [
                {
                    "type": self._entities[type(entity)],
                    **{k: v for k, v in entity.to_dict().items() if k != "_"},
                }
                for entity in event.entities
            ]
            if event.entities
            else []
        )

        message = {
            "entities": entities,
            "chatId": id_,
            "avatar": True,
            "from": {
                "id": id_,
                "first_name": (name or (sender.first_name if sender else None))
                or "Deleted Account",
                "last_name": last_name,
                "username": sender.username if sender else None,
                "language_code": "en",
                "title": name,
                "name": name or "Unknown",
                "type": type_,
            },
            "text": event.raw_text,
            "replyMessage": reply,
        }

        if event.document and event.document.thumbs:
            file_ = await event.download_media(thumb=-1)
            uri = await telegraph(file_)
            message["media"] = {"url": uri}

        return message

    async def create_quotly(
        self,
        event,
        url="https://quote-api.example.com/generate",
        reply={},
        bg=None,
        sender=None,
        OQAPI=True,
        file_name="quote.webp",
    ):
        if not isinstance(event, list):
            event = [event]
        if OQAPI:
            url = Quotly._API
        bg = bg or "#1b1429"
        content = {
            "type": "quote",
            "format": "webp",
            "backgroundColor": bg,
            "width": 512,
            "height": 768,
            "scale": 2,
            "messages": [
                await self._format_quote(message, reply=reply, sender=sender)
                for message in event
            ],
        }
        try:
            request = await async_searcher(url, post=True, json=content, re_json=True)
        except ContentTypeError as er:
            if url != self._API:
                return await self.create_quotly(
                    self._API, post=True, json=content, re_json=True
                )
            raise er

        if request.get("ok"):
            with open(file_name, "wb") as file:
                image = base64.decodebytes(request["result"]["image"].encode("utf-8"))
                file.write(image)
            return file_name
        raise Exception(str(request))


quotly = Quotly()


async def async_searcher(
    url: str,
    post: bool = None,
    headers: dict = None,
    params: dict = None,
    json: dict = None,
    data: dict = None,
    ssl=None,
    re_json: bool = False,
    re_content: bool = False,
    real: bool = False,
    *args,
    **kwargs
):
    try:
        import aiohttp
    except ImportError:
        raise DependencyMissingError(
            "'aiohttp' is not installed!\nThis function requires aiohttp to be installed."
        )

    async with aiohttp.ClientSession(headers=headers) as client:
        data = await (
            client.post(url, json=json, data=data, ssl=ssl, *args, **kwargs)
            if post
            else client.get(url, params=params, ssl=ssl, *args, **kwargs)
        )
        return await (
            data.json() if re_json else data.read() if re_content else data.text()
        )


@register(pattern="^/q(?: |$)(.*)")
async def quott_(event):
    match = event.pattern_match.group(1).strip()
    if not event.is_reply:
        return await event.reply("Please reply to a message.")

    msg = await event.reply("Creating quote, please wait.")
    reply = await event.get_reply_message()
    replied_to, reply_ = None, None

    if match:
        spli_ = match.split(maxsplit=1)
        if (spli_[0] in ["r", "reply"]) or (
            spli_[0].isdigit() and int(spli_[0]) in range(1, 21)
        ):
            if spli_[0].isdigit():
                if not event.client.is_bot:
                    reply_ = await event.client.get_messages(
                        event.chat_id,
                        min_id=event.reply_to_msg_id - 1,
                        reverse=True,
                        limit=int(spli_[0]),
                    )
                else:
                    id_ = reply.id
                    reply_ = []
                    for msg_ in range(id_, id_ + int(spli_[0])):
                        msh = await event.client.get_messages(event.chat_id, ids=msg_)
                        if msh:
                            reply_.append(msh)
            else:
                replied_to = await reply.get_reply_message()
            try:
                match = spli_[1]
            except IndexError:
                match = None

    user = None

    if not reply_:
        reply_ = reply

    if match:
        match = match.split(maxsplit=1)

    if match:
        if match[0].startswith("@") or match[0].isdigit():
            try:
                match_ = await event.client.parse_id(match[0])
                user = await event.client.get_entity(match_)
            except ValueError:
                pass
            match = match[1] if len(match) == 2 else None
        else:
            match = match[0]

    if match == "random":
        match = choice(all_col)

    try:
        file = await quotly.create_quotly(
            reply_, bg=match, reply=replied_to, sender=user
        )
    except Exception as er:
        return await msg.edit(str(er))

    message = await reply.reply("", file=file)
    os.remove(file)
    await msg.delete()
    return message


# <=================================================== HELP ====================================================>


__mod_name__ = "QUOTELY"

__help__ = """   
»  /q : Create quote.

» /q r : Get replied quote.

» /q 2 ᴛᴏ 8 : Get multiple quotes.

» /q < any colour name > : Create any coloured quotes.

➠ Example:

» /q red , /q blue etc.
"""
# <================================================ END =======================================================>
