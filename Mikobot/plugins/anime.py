# <============================================== IMPORTS =========================================================>
import asyncio
import json
import logging
import os
import random
import re
import shlex
import time
from datetime import datetime
from os.path import basename
from time import time
from traceback import format_exc as err
from typing import Optional, Tuple
from urllib.parse import quote
from uuid import uuid4

import requests
import urllib3
from bs4 import BeautifulSoup
from motor.core import AgnosticClient, AgnosticCollection, AgnosticDatabase
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.errors import (
    FloodWait,
    MessageNotModified,
    UserNotParticipant,
    WebpageCurlFailed,
    WebpageMediaEmpty,
)
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
)

from Mikobot import BOT_USERNAME, MESSAGE_DUMP, MONGO_DB_URI, app
from Mikobot.utils.custom_filters import PREFIX_HANDLER

# <=======================================================================================================>

FILLERS = {}

BOT_OWNER = list({int(x) for x in ("5907205317").split()})

_MGCLIENT: AgnosticClient = AsyncIOMotorClient(MONGO_DB_URI)

_DATABASE: AgnosticDatabase = _MGCLIENT["MikobotAnime"]


def get_collection(name: str) -> AgnosticCollection:
    """Create or Get Collection from your database"""
    return _DATABASE[name]


def _close_db() -> None:
    _MGCLIENT.close()


GROUPS = get_collection("GROUPS")
SFW_GRPS = get_collection("SFW_GROUPS")
DC = get_collection("DISABLED_CMDS")
AG = get_collection("AIRING_GROUPS")
CG = get_collection("CRUNCHY_GROUPS")
SG = get_collection("SUBSPLEASE_GROUPS")
HD = get_collection("HEADLINES_GROUPS")
MHD = get_collection("MAL_HEADLINES_GROUPS")
CHAT_OWNER = ChatMemberStatus.OWNER
MEMBER = ChatMemberStatus.MEMBER
ADMINISTRATOR = ChatMemberStatus.ADMINISTRATOR

failed_pic = "https://telegra.ph/file/09733b49f3a9d5b147d21.png"
no_pic = [
    "https://telegra.ph/file/0d2097f442e816ba3f946.jpg",
    "https://telegra.ph/file/5a152016056308ef63226.jpg",
    "https://telegra.ph/file/d2bf913b18688c59828e9.jpg",
    "https://telegra.ph/file/d53083ea69e84e3b54735.jpg",
    "https://telegra.ph/file/b5eb1e3606b7d2f1b491f.jpg",
]


DOWN_PATH = "Mikobot/downloads/"

AUTH_USERS = get_collection("AUTH_USERS")
IGNORE = get_collection("IGNORED_USERS")
PIC_DB = get_collection("PIC_DB")
GROUPS = get_collection("GROUPS")
CC = get_collection("CONNECTED_CHANNELS")
USER_JSON = {}
USER_WC = {}

LANGUAGES = {
    "af": "afrikaans",
    "sq": "albanian",
    "am": "amharic",
    "ar": "arabic",
    "hy": "armenian",
    "az": "azerbaijani",
    "eu": "basque",
    "be": "belarusian",
    "bn": "bengali",
    "bs": "bosnian",
    "bg": "bulgarian",
    "ca": "catalan",
    "ceb": "cebuano",
    "ny": "chichewa",
    "zh-cn": "chinese (simplified)",
    "zh-tw": "chinese (traditional)",
    "co": "corsican",
    "hr": "croatian",
    "cs": "czech",
    "da": "danish",
    "nl": "dutch",
    "en": "english",
    "eo": "esperanto",
    "et": "estonian",
    "tl": "filipino",
    "fi": "finnish",
    "fr": "french",
    "fy": "frisian",
    "gl": "galician",
    "ka": "georgian",
    "de": "german",
    "el": "greek",
    "gu": "gujarati",
    "ht": "haitian creole",
    "ha": "hausa",
    "haw": "hawaiian",
    "iw": "hebrew",
    "he": "hebrew",
    "hi": "hindi",
    "hmn": "hmong",
    "hu": "hungarian",
    "is": "icelandic",
    "ig": "igbo",
    "id": "indonesian",
    "ga": "irish",
    "it": "italian",
    "ja": "japanese",
    "jw": "javanese",
    "kn": "kannada",
    "kk": "kazakh",
    "km": "khmer",
    "ko": "korean",
    "ku": "kurdish (kurmanji)",
    "ky": "kyrgyz",
    "lo": "lao",
    "la": "latin",
    "lv": "latvian",
    "lt": "lithuanian",
    "lb": "luxembourgish",
    "mk": "macedonian",
    "mg": "malagasy",
    "ms": "malay",
    "ml": "malayalam",
    "mt": "maltese",
    "mi": "maori",
    "mr": "marathi",
    "mn": "mongolian",
    "my": "myanmar (burmese)",
    "ne": "nepali",
    "no": "norwegian",
    "or": "odia",
    "ps": "pashto",
    "fa": "persian",
    "pl": "polish",
    "pt": "portuguese",
    "pa": "punjabi",
    "ro": "romanian",
    "ru": "russian",
    "sm": "samoan",
    "gd": "scots gaelic",
    "sr": "serbian",
    "st": "sesotho",
    "sn": "shona",
    "sd": "sindhi",
    "si": "sinhala",
    "sk": "slovak",
    "sl": "slovenian",
    "so": "somali",
    "es": "spanish",
    "su": "sundanese",
    "sw": "swahili",
    "sv": "swedish",
    "tg": "tajik",
    "ta": "tamil",
    "tt": "tatar",
    "te": "telugu",
    "th": "thai",
    "tr": "turkish",
    "tk": "turkmen",
    "uk": "ukrainian",
    "ur": "urdu",
    "ug": "uyghur",
    "uz": "uzbek",
    "vi": "vietnamese",
    "cy": "welsh",
    "xh": "xhosa",
    "yi": "yiddish",
    "yo": "yoruba",
    "zu": "zulu",
}

DEFAULT_SERVICE_URLS = (
    "translate.google.ac",
    "translate.google.ad",
    "translate.google.ae",
    "translate.google.al",
    "translate.google.am",
    "translate.google.as",
    "translate.google.at",
    "translate.google.az",
    "translate.google.ba",
    "translate.google.be",
    "translate.google.bf",
    "translate.google.bg",
    "translate.google.bi",
    "translate.google.bj",
    "translate.google.bs",
    "translate.google.bt",
    "translate.google.by",
    "translate.google.ca",
    "translate.google.cat",
    "translate.google.cc",
    "translate.google.cd",
    "translate.google.cf",
    "translate.google.cg",
    "translate.google.ch",
    "translate.google.ci",
    "translate.google.cl",
    "translate.google.cm",
    "translate.google.cn",
    "translate.google.co.ao",
    "translate.google.co.bw",
    "translate.google.co.ck",
    "translate.google.co.cr",
    "translate.google.co.id",
    "translate.google.co.il",
    "translate.google.co.in",
    "translate.google.co.jp",
    "translate.google.co.ke",
    "translate.google.co.kr",
    "translate.google.co.ls",
    "translate.google.co.ma",
    "translate.google.co.mz",
    "translate.google.co.nz",
    "translate.google.co.th",
    "translate.google.co.tz",
    "translate.google.co.ug",
    "translate.google.co.uk",
    "translate.google.co.uz",
    "translate.google.co.ve",
    "translate.google.co.vi",
    "translate.google.co.za",
    "translate.google.co.zm",
    "translate.google.co.zw",
    "translate.google.co",
    "translate.google.com.af",
    "translate.google.com.ag",
    "translate.google.com.ai",
    "translate.google.com.ar",
    "translate.google.com.au",
    "translate.google.com.bd",
    "translate.google.com.bh",
    "translate.google.com.bn",
    "translate.google.com.bo",
    "translate.google.com.br",
    "translate.google.com.bz",
    "translate.google.com.co",
    "translate.google.com.cu",
    "translate.google.com.cy",
    "translate.google.com.do",
    "translate.google.com.ec",
    "translate.google.com.eg",
    "translate.google.com.et",
    "translate.google.com.fj",
    "translate.google.com.gh",
    "translate.google.com.gi",
    "translate.google.com.gt",
    "translate.google.com.hk",
    "translate.google.com.jm",
    "translate.google.com.kh",
    "translate.google.com.kw",
    "translate.google.com.lb",
    "translate.google.com.lc",
    "translate.google.com.ly",
    "translate.google.com.mm",
    "translate.google.com.mt",
    "translate.google.com.mx",
    "translate.google.com.my",
    "translate.google.com.na",
    "translate.google.com.ng",
    "translate.google.com.ni",
    "translate.google.com.np",
    "translate.google.com.om",
    "translate.google.com.pa",
    "translate.google.com.pe",
    "translate.google.com.pg",
    "translate.google.com.ph",
    "translate.google.com.pk",
    "translate.google.com.pr",
    "translate.google.com.py",
    "translate.google.com.qa",
    "translate.google.com.sa",
    "translate.google.com.sb",
    "translate.google.com.sg",
    "translate.google.com.sl",
    "translate.google.com.sv",
    "translate.google.com.tj",
    "translate.google.com.tr",
    "translate.google.com.tw",
    "translate.google.com.ua",
    "translate.google.com.uy",
    "translate.google.com.vc",
    "translate.google.com.vn",
    "translate.google.com",
    "translate.google.cv",
    "translate.google.cx",
    "translate.google.cz",
    "translate.google.de",
    "translate.google.dj",
    "translate.google.dk",
    "translate.google.dm",
    "translate.google.dz",
    "translate.google.ee",
    "translate.google.es",
    "translate.google.eu",
    "translate.google.fi",
    "translate.google.fm",
    "translate.google.fr",
    "translate.google.ga",
    "translate.google.ge",
    "translate.google.gf",
    "translate.google.gg",
    "translate.google.gl",
    "translate.google.gm",
    "translate.google.gp",
    "translate.google.gr",
    "translate.google.gy",
    "translate.google.hn",
    "translate.google.hr",
    "translate.google.ht",
    "translate.google.hu",
    "translate.google.ie",
    "translate.google.im",
    "translate.google.io",
    "translate.google.iq",
    "translate.google.is",
    "translate.google.it",
    "translate.google.je",
    "translate.google.jo",
    "translate.google.kg",
    "translate.google.ki",
    "translate.google.kz",
    "translate.google.la",
    "translate.google.li",
    "translate.google.lk",
    "translate.google.lt",
    "translate.google.lu",
    "translate.google.lv",
    "translate.google.md",
    "translate.google.me",
    "translate.google.mg",
    "translate.google.mk",
    "translate.google.ml",
    "translate.google.mn",
    "translate.google.ms",
    "translate.google.mu",
    "translate.google.mv",
    "translate.google.mw",
    "translate.google.ne",
    "translate.google.nf",
    "translate.google.nl",
    "translate.google.no",
    "translate.google.nr",
    "translate.google.nu",
    "translate.google.pl",
    "translate.google.pn",
    "translate.google.ps",
    "translate.google.pt",
    "translate.google.ro",
    "translate.google.rs",
    "translate.google.ru",
    "translate.google.rw",
    "translate.google.sc",
    "translate.google.se",
    "translate.google.sh",
    "translate.google.si",
    "translate.google.sk",
    "translate.google.sm",
    "translate.google.sn",
    "translate.google.so",
    "translate.google.sr",
    "translate.google.st",
    "translate.google.td",
    "translate.google.tg",
    "translate.google.tk",
    "translate.google.tl",
    "translate.google.tm",
    "translate.google.tn",
    "translate.google.to",
    "translate.google.tt",
    "translate.google.us",
    "translate.google.vg",
    "translate.google.vu",
    "translate.google.ws",
)
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URLS_SUFFIX = [
    re.search("translate.google.(.*)", url.strip()).group(1)
    for url in DEFAULT_SERVICE_URLS
]
URL_SUFFIX_DEFAULT = "cn"


def rand_key():
    return str(uuid4())[:8]


def control_user(func):
    async def wrapper(_, message: Message):
        msg = json.loads(str(message))
        gid = msg["chat"]["id"]
        gidtype = msg["chat"]["type"]
        if gidtype in [ChatType.SUPERGROUP, ChatType.GROUP] and not (
            await GROUPS.find_one({"_id": gid})
        ):
            try:
                gidtitle = msg["chat"]["username"]
            except KeyError:
                gidtitle = msg["chat"]["title"]
            await GROUPS.insert_one({"_id": gid, "grp": gidtitle})
            await clog(
                "Mikobot",
                f"Bot added to a new group\n\n{gidtitle}\nID: `{gid}`",
                "NEW_GROUP",
            )
        try:
            user = msg["from_user"]["id"]
        except KeyError:
            user = msg["chat"]["id"]
        if await IGNORE.find_one({"_id": user}):
            return
        nut = time()
        if user not in BOT_OWNER:
            try:
                out = USER_JSON[user]
                if nut - out < 1.2:
                    USER_WC[user] += 1
                    if USER_WC[user] == 3:
                        await message.reply_text(
                            ("Stop spamming bot!!!" + "\nElse you will be blacklisted"),
                        )
                        await clog("Mikobot", f"UserID: {user}", "SPAM")
                    if USER_WC[user] == 5:
                        await IGNORE.insert_one({"_id": user})
                        await message.reply_text(
                            (
                                "You have been exempted from using this bot "
                                + "now due to spamming 5 times consecutively!!!"
                                + "\nTo remove restriction plead to "
                                + "@ProjectCodeXSupport"
                            )
                        )
                        await clog("Mikobot", f"UserID: {user}", "BAN")
                        return
                    await asyncio.sleep(USER_WC[user])
                else:
                    USER_WC[user] = 0
            except KeyError:
                pass
            USER_JSON[user] = nut
        try:
            await func(_, message, msg)
        except FloodWait as e:
            await asyncio.sleep(e.x + 5)
        except MessageNotModified:
            pass
        except Exception:
            e = err()
            reply_msg = None
            if func.__name__ == "trace_bek":
                reply_msg = message.reply_to_message
            try:
                await clog(
                    "Mikobot",
                    "Message:\n" + msg["text"] + "\n\n" + "```" + e + "```",
                    "COMMAND",
                    msg=message,
                    replied=reply_msg,
                )
            except Exception:
                await clog("Mikobot", e, "FAILURE", msg=message)

    return wrapper


def check_user(func):
    async def wrapper(_, c_q: CallbackQuery):
        cq = json.loads(str(c_q))
        user = cq["from_user"]["id"]
        if await IGNORE.find_one({"_id": user}):
            return
        cqowner_is_ch = False
        cqowner = cq["data"].split("_").pop()
        if "-100" in cqowner:
            cqowner_is_ch = True
            ccdata = await CC.find_one({"_id": cqowner})
            if ccdata and ccdata["usr"] == user:
                user_valid = True
            else:
                user_valid = False
        if user in BOT_OWNER or user == int(cqowner):
            if user not in BOT_OWNER:
                nt = time()
                try:
                    ot = USER_JSON[user]
                    if nt - ot < 1.4:
                        await c_q.answer(
                            ("Stop spamming bot!!!\n" + "Else you will be blacklisted"),
                            show_alert=True,
                        )
                        await clog("Mikobot", f"UserID: {user}", "SPAM")
                except KeyError:
                    pass
                USER_JSON[user] = nt
            try:
                await func(_, c_q, cq)
            except FloodWait as e:
                await asyncio.sleep(e.x + 5)
            except MessageNotModified:
                pass
            except Exception:
                e = err()
                reply_msg = None
                if func.__name__ == "tracemoe_btn":
                    reply_msg = c_q.message.reply_to_message
                try:
                    await clog(
                        "Mikobot",
                        "Callback:\n" + cq["data"] + "\n\n" + "```" + e + "```",
                        "CALLBACK",
                        cq=c_q,
                        replied=reply_msg,
                    )
                except Exception:
                    await clog("Mikobot", e, "FAILURE", cq=c_q)
        else:
            if cqowner_is_ch:
                if user_valid:
                    try:
                        await func(_, c_q, cq)
                    except FloodWait as e:
                        await asyncio.sleep(e.x + 5)
                    except MessageNotModified:
                        pass
                    except Exception:
                        e = err()
                        reply_msg = None
                        if func.__name__ == "tracemoe_btn":
                            reply_msg = c_q.message.reply_to_message
                        try:
                            await clog(
                                "Mikobot",
                                "Callback:\n" + cq["data"] + "\n\n" + "```" + e + "```",
                                "CALLBACK_ANON",
                                cq=c_q,
                                replied=reply_msg,
                            )
                        except Exception:
                            await clog("Mikobot", e, "FAILURE", cq=c_q)
                else:
                    await c_q.answer(
                        (
                            "No one can click buttons on queries made by "
                            + "channels unless connected with /aniconnect!!!"
                        ),
                        show_alert=True,
                    )
            else:
                await c_q.answer(
                    "Not your query!!!",
                    show_alert=True,
                )

    return wrapper


async def media_to_image(client: app, message: Message, x: Message, replied: Message):
    if not (replied.photo or replied.sticker or replied.animation or replied.video):
        await x.edit_text("Media Type Is Invalid !")
        await asyncio.sleep(5)
        await x.delete()
        return
    media = replied.photo or replied.sticker or replied.animation or replied.video
    if not os.path.isdir(DOWN_PATH):
        os.makedirs(DOWN_PATH)
    dls = await client.download_media(
        media,
        file_name=DOWN_PATH + rand_key(),
    )
    dls_loc = os.path.join(DOWN_PATH, os.path.basename(dls))
    if replied.sticker and replied.sticker.file_name.endswith(".tgs"):
        png_file = os.path.join(DOWN_PATH, f"{rand_key()}.png")
        cmd = (
            f"lottie_convert.py --frame 0 -if lottie " + f"-of png {dls_loc} {png_file}"
        )
        stdout, stderr = (await runcmd(cmd))[:2]
        os.remove(dls_loc)
        if not os.path.lexists(png_file):
            await x.edit_text("This sticker is Gey, Task Failed Successfully ≧ω≦")
            await asyncio.sleep(5)
            await x.delete()
            raise Exception(stdout + stderr)
        dls_loc = png_file
    elif replied.sticker and replied.sticker.file_name.endswith(".webp"):
        stkr_file = os.path.join(DOWN_PATH, f"{rand_key()}.png")
        os.rename(dls_loc, stkr_file)
        if not os.path.lexists(stkr_file):
            await x.edit_text("```Sticker not found...```")
            await asyncio.sleep(5)
            await x.delete()
            return
        dls_loc = stkr_file
    elif replied.animation or replied.video:
        await x.edit_text("`Converting Media To Image ...`")
        jpg_file = os.path.join(DOWN_PATH, f"{rand_key()}.jpg")
        await take_screen_shot(dls_loc, 0, jpg_file)
        os.remove(dls_loc)
        if not os.path.lexists(jpg_file):
            await x.edit_text("This Gif is Gey (｡ì _ í｡), Task Failed Successfully !")
            await asyncio.sleep(5)
            await x.delete()
            return
        dls_loc = jpg_file
    return dls_loc


async def runcmd(cmd: str) -> Tuple[str, str, int, int]:
    """run command in terminal"""
    args = shlex.split(cmd)
    process = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return (
        stdout.decode("utf-8", "replace").strip(),
        stderr.decode("utf-8", "replace").strip(),
        process.returncode,
        process.pid,
    )


async def take_screen_shot(
    video_file: str, duration: int, path: str = ""
) -> Optional[str]:
    """take a screenshot"""
    print(
        "[[[Extracting a frame from %s ||| Video duration => %s]]]",
        video_file,
        duration,
    )
    thumb_image_path = path or os.path.join(DOWN_PATH, f"{basename(video_file)}.jpg")
    command = (
        f"ffmpeg -ss {duration} " + f'-i "{video_file}" -vframes 1 "{thumb_image_path}"'
    )
    err = (await runcmd(command))[1]
    if err:
        print(err)
    return thumb_image_path if os.path.exists(thumb_image_path) else None


async def get_user_from_channel(cid):
    try:
        k = (await CC.find_one({"_id": str(cid)}))["usr"]
        return k
    except TypeError:
        return None


async def return_json_senpai(
    query: str, vars_: dict, auth: bool = False, user: int = None
):
    url = "https://graphql.anilist.co"
    headers = None
    if auth:
        headers = {
            "Authorization": (
                "Bearer " + str((await AUTH_USERS.find_one({"id": int(user)}))["token"])
            ),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    return requests.post(
        url, json={"query": query, "variables": vars_}, headers=headers
    ).json()


def cflag(country):
    if country == "JP":
        return "\U0001F1EF\U0001F1F5"
    if country == "CN":
        return "\U0001F1E8\U0001F1F3"
    if country == "KR":
        return "\U0001F1F0\U0001F1F7"
    if country == "TW":
        return "\U0001F1F9\U0001F1FC"


def pos_no(no):
    ep_ = list(str(no))
    x = ep_.pop()
    if ep_ != [] and ep_.pop() == "1":
        return "th"
    th = "st" if x == "1" else "nd" if x == "2" else "rd" if x == "3" else "th"
    return th


def make_it_rw(time_stamp):
    """Converting Time Stamp to Readable Format"""
    seconds, milliseconds = divmod(int(time_stamp), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((str(days) + " Days, ") if days else "")
        + ((str(hours) + " Hours, ") if hours else "")
        + ((str(minutes) + " Minutes, ") if minutes else "")
        + ((str(seconds) + " Seconds, ") if seconds else "")
        + ((str(milliseconds) + " ms, ") if milliseconds else "")
    )
    return tmp[:-2]


async def clog(
    name: str,
    text: str,
    tag: str,
    msg: Message = None,
    cq: CallbackQuery = None,
    replied: Message = None,
    file: str = None,
    send_as_file: str = None,
):
    log = f"#{name.upper()}  #{tag.upper()}\n\n{text}"
    data = ""
    if msg:
        data += str(msg)
        data += "\n\n\n\n"
    if cq:
        data += str(cq)
        data += "\n\n\n\n"
    await app.send_message(chat_id=MESSAGE_DUMP, text=log)
    if msg or cq:
        with open("query_data.txt", "x") as output:
            output.write(data)
        await app.send_document(MESSAGE_DUMP, "query_data.txt")
        os.remove("query_data.txt")
    if replied:
        media = replied.photo or replied.sticker or replied.animation or replied.video
        media_path = await app.download_media(media)
        await app.send_document(MESSAGE_DUMP, media_path)
    if file:
        await app.send_document(MESSAGE_DUMP, file)
    if send_as_file:
        with open("dataInQuestio.txt", "x") as text_file:
            text_file.write()
        await app.send_document(MESSAGE_DUMP, "dataInQuestio.txt")
        os.remove("dataInQuestio.txt")


def get_btns(
    media,
    user: int,
    result: list,
    lsqry: str = None,
    lspage: int = None,
    auth: bool = False,
    sfw: str = "False",
):
    buttons = []
    qry = f"_{lsqry}" if lsqry is not None else ""
    pg = f"_{lspage}" if lspage is not None else ""
    if media == "ANIME" and sfw == "False":
        buttons.append(
            [
                InlineKeyboardButton(
                    text="Characters",
                    callback_data=(
                        f"char_{result[2][0]}_ANI" + f"{qry}{pg}_{str(auth)}_1_{user}"
                    ),
                ),
                InlineKeyboardButton(
                    text="Description",
                    callback_data=(
                        f"desc_{result[2][0]}_ANI" + f"{qry}{pg}_{str(auth)}_{user}"
                    ),
                ),
                InlineKeyboardButton(
                    text="List Series",
                    callback_data=(
                        f"ls_{result[2][0]}_ANI" + f"{qry}{pg}_{str(auth)}_{user}"
                    ),
                ),
            ]
        )
    if media == "CHARACTER":
        buttons.append(
            [
                InlineKeyboardButton(
                    "Description",
                    callback_data=(
                        f"desc_{result[2][0]}_CHAR" + f"{qry}{pg}_{str(auth)}_{user}"
                    ),
                )
            ]
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    "List Series",
                    callback_data=f"lsc_{result[2][0]}{qry}{pg}_{str(auth)}_{user}",
                )
            ]
        )
    if media == "SCHEDULED":
        if result[0] != 0 and result[0] != 6:
            buttons.append(
                [
                    InlineKeyboardButton(
                        str(day_(result[0] - 1)),
                        callback_data=f"sched_{result[0]-1}_{user}",
                    ),
                    InlineKeyboardButton(
                        str(day_(result[0] + 1)),
                        callback_data=f"sched_{result[0]+1}_{user}",
                    ),
                ]
            )
        if result[0] == 0:
            buttons.append(
                [
                    InlineKeyboardButton(
                        str(day_(result[0] + 1)),
                        callback_data=f"sched_{result[0]+1}_{user}",
                    )
                ]
            )
        if result[0] == 6:
            buttons.append(
                [
                    InlineKeyboardButton(
                        str(day_(result[0] - 1)),
                        callback_data=f"sched_{result[0]-1}_{user}",
                    )
                ]
            )
    if media == "MANGA" and sfw == "False":
        buttons.append([InlineKeyboardButton("More Info", url=result[1][2])])
    if media == "AIRING" and sfw == "False":
        buttons.append([InlineKeyboardButton("More Info", url=result[1][0])])
    if auth is True and media != "SCHEDULED" and sfw == "False":
        auth_btns = get_auth_btns(media, user, result[2], lspage=lspage, lsqry=lsqry)
        buttons.append(auth_btns)
    if len(result) > 3:
        if result[3] == "None":
            if result[4] != "None":
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text="Sequel",
                            callback_data=f"btn_{result[4]}_{str(auth)}_{user}",
                        )
                    ]
                )
        else:
            if result[4] != "None":
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text="Prequel",
                            callback_data=f"btn_{result[3]}_{str(auth)}_{user}",
                        ),
                        InlineKeyboardButton(
                            text="Sequel",
                            callback_data=f"btn_{result[4]}_{str(auth)}_{user}",
                        ),
                    ]
                )
            else:
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text="Prequel",
                            callback_data=f"btn_{result[3]}_{str(auth)}_{user}",
                        )
                    ]
                )
    if (lsqry is not None) and (len(result) != 1):
        if lspage == 1:
            if result[1][1] is True:
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text="Next",
                            callback_data=(
                                f"page_{media}{qry}_{int(lspage)+1}_{str(auth)}_{user}"
                            ),
                        )
                    ]
                )
            else:
                pass
        elif lspage != 1:
            if result[1][1] is False:
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text="Prev",
                            callback_data=(
                                f"page_{media}{qry}_{int(lspage)-1}_{str(auth)}_{user}"
                            ),
                        )
                    ]
                )
            else:
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text="Prev",
                            callback_data=(
                                f"page_{media}{qry}_{int(lspage)-1}_{str(auth)}_{user}"
                            ),
                        ),
                        InlineKeyboardButton(
                            text="Next",
                            callback_data=(
                                f"page_{media}{qry}_{int(lspage)+1}_{str(auth)}_{user}"
                            ),
                        ),
                    ]
                )
    return InlineKeyboardMarkup(buttons)


def get_auth_btns(media, user, data, lsqry: str = None, lspage: int = None):
    btn = []
    qry = f"_{lsqry}" if lsqry is not None else ""
    pg = f"_{lspage}" if lspage is not None else ""
    if media == "CHARACTER":
        btn.append(
            InlineKeyboardButton(
                text=("Add to Favs" if data[1] is not True else "Remove from Favs"),
                callback_data=f"fav_{media}_{data[0]}{qry}{pg}_{user}",
            )
        )
    else:
        btn.append(
            InlineKeyboardButton(
                text=("Add to Favs" if data[3] is not True else "Remove from Favs"),
                callback_data=f"fav_{media}_{data[0]}{qry}{pg}_{user}",
            )
        )
        btn.append(
            InlineKeyboardButton(
                text="Add to List" if data[1] is False else "Update in List",
                callback_data=(
                    f"lsadd_{media}_{data[0]}{qry}{pg}_{user}"
                    if data[1] is False
                    else f"lsupdt_{media}_{data[0]}_{data[2]}{qry}{pg}_{user}"
                ),
            )
        )
    return btn


def day_(x: int):
    if x == 0:
        return "Monday"
    if x == 1:
        return "Tuesday"
    if x == 2:
        return "Wednesday"
    if x == 3:
        return "Thursday"
    if x == 4:
        return "Friday"
    if x == 5:
        return "Saturday"
    if x == 6:
        return "Sunday"


def season_(future: bool = False):
    k = datetime.now()
    m = k.month
    if future:
        m = m + 3
    y = k.year
    if m > 12:
        y = y + 1
    if m in [1, 2, 3] or m > 12:
        return "WINTER", y
    if m in [4, 5, 6]:
        return "SPRING", y
    if m in [7, 8, 9]:
        return "SUMMER", y
    if m in [10, 11, 12]:
        return "FALL", y


class google_new_transError(Exception):
    """Exception that uses context to present a meaningful error message"""

    def __init__(self, msg=None, **kwargs):
        self.tts = kwargs.pop("tts", None)
        self.rsp = kwargs.pop("response", None)
        if msg:
            self.msg = msg
        elif self.tts is not None:
            self.msg = self.infer_msg(self.tts, self.rsp)
        else:
            self.msg = None
        super(google_new_transError, self).__init__(self.msg)

    def infer_msg(self, tts, rsp=None):
        cause = "Unknown"

        if rsp is None:
            premise = "Failed to connect"

            return "{}. Probable cause: {}".format(premise, "timeout")
            # if tts.tld != 'com':
            #     host = _translate_url(tld=tts.tld)
            #     cause = "Host '{}' is not reachable".format(host)

        else:
            status = rsp.status_code
            reason = rsp.reason

            premise = "{:d} ({}) from TTS API".format(status, reason)

            if status == 403:
                cause = "Bad token or upstream API changes"
            elif status == 200 and not tts.lang_check:
                cause = (
                    "No audio stream in response. Unsupported language '%s'"
                    % self.tts.lang
                )
            elif status >= 500:
                cause = "Uptream API error. Try again later."

        return "{}. Probable cause: {}".format(premise, cause)


class google_translator:
    """
    You can use 108 language in target and source,details view LANGUAGES.
    Target language: like 'en'、'zh'、'th'...
    :param url_suffix: The source text(s) to be translated. Batch translation is supported via sequence input.
                       The value should be one of the url_suffix listed in : `DEFAULT_SERVICE_URLS`
    :type url_suffix: UTF-8 :class:`str`; :class:`unicode`; string sequence (list, tuple, iterator, generator)
    :param text: The source text(s) to be translated.
    :type text: UTF-8 :class:`str`; :class:`unicode`;
    :param lang_tgt: The language to translate the source text into.
                     The value should be one of the language codes listed in : `LANGUAGES`
    :type lang_tgt: :class:`str`; :class:`unicode`
    :param lang_src: The language of the source text.
                    The value should be one of the language codes listed in :const:`googletrans.LANGUAGES`
                    If a language is not specified,
                    the system will attempt to identify the source language automatically.
    :type lang_src: :class:`str`; :class:`unicode`
    :param timeout: Timeout Will be used for every request.
    :type timeout: number or a double of numbers
    :param proxies: proxies Will be used for every request.
    :type proxies: class : dict; like: {'http': 'http:171.112.169.47:19934/', 'https': 'https:171.112.169.47:19934/'}
    """

    def __init__(self, url_suffix="cn", timeout=5, proxies=None):
        self.proxies = proxies
        if url_suffix not in URLS_SUFFIX:
            self.url_suffix = URL_SUFFIX_DEFAULT
        else:
            self.url_suffix = url_suffix
        url_base = "https://translate.google.{}".format(self.url_suffix)
        self.url = url_base + "/_/TranslateWebserverUi/data/batchexecute"
        self.timeout = timeout

    def _package_rpc(self, text, lang_src="auto", lang_tgt="auto"):
        GOOGLE_TTS_RPC = ["MkEWBc"]
        parameter = [[text.strip(), lang_src, lang_tgt, True], [1]]
        escaped_parameter = json.dumps(parameter, separators=(",", ":"))
        rpc = [[[random.choice(GOOGLE_TTS_RPC), escaped_parameter, None, "generic"]]]
        espaced_rpc = json.dumps(rpc, separators=(",", ":"))
        # text_urldecode = quote(text.strip())
        freq_initial = "f.req={}&".format(quote(espaced_rpc))
        freq = freq_initial
        return freq

    def translate(self, text, lang_tgt="auto", lang_src="auto", pronounce=False):
        try:
            lang = LANGUAGES[lang_src]
        except Exception:
            lang_src = "auto"
        try:
            lang = LANGUAGES[lang_tgt]
        except Exception:
            lang_src = "auto"
        text = str(text)
        if len(text) >= 5000:
            return "Warning: Can only detect less than 5000 characters"
        if len(text) == 0:
            return ""
        headers = {
            "Referer": "http://translate.google.{}/".format(self.url_suffix),
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/47.0.2526.106 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        }
        freq = self._package_rpc(text, lang_src, lang_tgt)
        response = requests.Request(
            method="POST",
            url=self.url,
            data=freq,
            headers=headers,
        )
        try:
            if self.proxies is None or type(self.proxies) != dict:
                self.proxies = {}
            with requests.Session() as s:
                s.proxies = self.proxies
                r = s.send(
                    request=response.prepare(), verify=False, timeout=self.timeout
                )
            for line in r.iter_lines(chunk_size=1024):
                decoded_line = line.decode("utf-8")
                if "MkEWBc" in decoded_line:
                    try:
                        response = decoded_line
                        response = json.loads(response)
                        response = list(response)
                        response = json.loads(response[0][2])
                        response_ = list(response)
                        response = response_[1][0]
                        if len(response) == 1:
                            if len(response[0]) > 5:
                                sentences = response[0][5]
                            else:  ## only url
                                sentences = response[0][0]
                                if pronounce is False:
                                    return sentences
                                elif pronounce == True:
                                    return [sentences, None, None]
                            translate_text = ""
                            for sentence in sentences:
                                sentence = sentence[0]
                                translate_text += sentence.strip() + " "
                            translate_text = translate_text
                            if pronounce is False:
                                return translate_text
                            elif pronounce == True:
                                pronounce_src = response_[0][0]
                                pronounce_tgt = response_[1][0][0][1]
                                return [translate_text, pronounce_src, pronounce_tgt]
                        elif len(response) == 2:
                            sentences = []
                            for i in response:
                                sentences.append(i[0])
                            if pronounce is False:
                                return sentences
                            elif pronounce == True:
                                pronounce_src = response_[0][0]
                                pronounce_tgt = response_[1][0][0][1]
                                return [sentences, pronounce_src, pronounce_tgt]
                    except Exception as e:
                        raise e
            r.raise_for_status()
        except requests.exceptions.ConnectTimeout as e:
            raise e
        except requests.exceptions.HTTPError as e:
            # Request successful, bad response
            raise google_new_transError(tts=self, response=r)
        except requests.exceptions.RequestException as e:
            # Request failed
            raise google_new_transError(tts=self)

    def detect(self, text):
        text = str(text)
        if len(text) >= 5000:
            return log.debug("Warning: Can only detect less than 5000 characters")
        if len(text) == 0:
            return ""
        headers = {
            "Referer": "http://translate.google.{}/".format(self.url_suffix),
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/47.0.2526.106 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        }
        freq = self._package_rpc(text)
        response = requests.Request(
            method="POST", url=self.url, data=freq, headers=headers
        )
        try:
            if self.proxies is None or type(self.proxies) != dict:
                self.proxies = {}
            with requests.Session() as s:
                s.proxies = self.proxies
                r = s.send(
                    request=response.prepare(), verify=False, timeout=self.timeout
                )

            for line in r.iter_lines(chunk_size=1024):
                decoded_line = line.decode("utf-8")
                if "MkEWBc" in decoded_line:
                    # regex_str = r"\[\[\"wrb.fr\",\"MkEWBc\",\"\[\[(.*).*?,\[\[\["
                    try:
                        # data_got = re.search(regex_str,decoded_line).group(1)
                        response = decoded_line
                        response = json.loads(response)
                        response = list(response)
                        response = json.loads(response[0][2])
                        response = list(response)
                        detect_lang = response[0][2]
                    except Exception:
                        raise Exception
                    # data_got = data_got.split('\\\"]')[0]
                    return [detect_lang, LANGUAGES[detect_lang.lower()]]
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            # Request successful, bad response
            log.debug(str(e))
            raise google_new_transError(tts=self, response=r)
        except requests.exceptions.RequestException as e:
            # Request failed
            log.debug(str(e))
            raise google_new_transError(tts=self)


async def uidata(id_):
    data = await GUI.find_one({"_id": str(id_)})
    if data is not None:
        bullet = str(data["bl"]) + " "
        if data["bl"] is None:
            bullet = ""
        return bullet, data["cs"]
    return ["➤ ", "UPPER"]


async def get_ui_text(case):
    if case == "UPPER":
        return [
            "SOURCE",
            "TYPE",
            "SCORE",
            "DURATION",
            "USER DATA",
            "ADULT RATED",
            "STATUS",
            "GENRES",
            "TAGS",
            "SEQUEL",
            "PREQUEL",
            "NEXT AIRING",
            "DESCRIPTION",
            "VOLUMES",
            "CHAPTERS",
        ]
    else:
        return [
            "Source",
            "Type",
            "Score",
            "Duration",
            "User Data",
            "Adult Rated",
            "Status",
            "Genres",
            "Tags",
            "Sequel",
            "Prequel",
            "Next Airing",
            "Description",
            "Volumes",
            "Chapters",
        ]


tr = google_translator()
ANIME_DB, MANGA_DB, CHAR_DB, STUDIO_DB, AIRING_DB = {}, {}, {}, {}, {}
GUI = get_collection("GROUP_UI")

#### Anilist part ####

ANIME_TEMPLATE = """{name}

**ID | MAL ID:** `{idm}` | `{idmal}`
{bl}**{psrc}:** `{source}`
{bl}**{ptype}:** `{formats}`{avscd}{dura}{user_data}
{status_air}{gnrs_}{tags_}

🎬 {trailer_link}
📖 <a href="{url}">Official Site</a>

{additional}"""


# GraphQL Queries.
ANIME_QUERY = """
query ($id: Int, $idMal:Int, $search: String) {
    Media (id: $id, idMal: $idMal, search: $search, type: ANIME) {
        id
        idMal
        title {
            romaji
            english
            native
        }
        format
        status
        episodes
        duration
        countryOfOrigin
        source (version: 2)
        trailer {
            id
            site
        }
        genres
        tags {
            name
        }
        averageScore
        relations {
            edges {
                node {
                    title {
                        romaji
                        english
                    }
                    id
                    type
                }
                relationType
            }
        }
        nextAiringEpisode {
            timeUntilAiring
            episode
        }
        isAdult
        isFavourite
        mediaListEntry {
            status
            score
            id
        }
        siteUrl
    }
}
"""

ISADULT = """
query ($id: Int) {
    Media (id: $id) {
        isAdult
    }
}
"""

BROWSE_QUERY = """
query ($s: MediaSeason, $y: Int, $sort: [MediaSort]) {
    Page {
        media (season: $s, seasonYear: $y, sort: $sort) {
    	    title {
                romaji
            }
            format
        }
    }
}
"""

FAV_ANI_QUERY = """
query ($id: Int, $page: Int) {
    User (id: $id) {
        favourites {
            anime (page: $page, perPage: 10) {
                pageInfo {
                    lastPage
                    hasNextPage
                }
                edges {
                    node {
                        title {
                            romaji
                        }
                        siteUrl
                    }
                }
            }
        }
    }
}
"""

FAV_MANGA_QUERY = """
query ($id: Int, $page: Int) {
    User (id: $id) {
        favourites {
            manga (page: $page, perPage: 10) {
                pageInfo {
                    lastPage
                    hasNextPage
                }
                edges {
                    node {
                        title {
                            romaji
                        }
                        siteUrl
                    }
                }
            }
        }
    }
}
"""

FAV_CHAR_QUERY = """
query ($id: Int, $page: Int) {
    User (id: $id) {
        favourites {
            characters (page: $page, perPage: 10) {
                pageInfo {
                    lastPage
                    hasNextPage
                }
                edges {
                    node {
                        name {
                            full
                        }
                        siteUrl
                    }
                }
            }
        }
    }
}
"""

VIEWER_QRY = """
query {
    Viewer {
        id
        name
        siteUrl
        statistics {
            anime {
                count
                minutesWatched
                episodesWatched
                meanScore
            }
            manga {
                count
                chaptersRead
                volumesRead
                meanScore
            }
        }
    }
}
"""

USER_QRY = """
query ($search: String) {
    User (name: $search) {
        id
        name
        siteUrl
        statistics {
            anime {
                count
                minutesWatched
                episodesWatched
                meanScore
            }
            manga {
                count
                chaptersRead
                volumesRead
                meanScore
            }
        }
    }
}
"""

ANIME_MUTATION = """
mutation ($id: Int) {
    ToggleFavourite (animeId: $id) {
        anime {
            pageInfo {
                total
            }
        }
    }
}   
"""

MANGA_MUTATION = """
mutation ($id: Int) {
    ToggleFavourite (mangaId: $id) {
        manga {
            pageInfo {
                total
            }
        }
    }
}
"""

STUDIO_MUTATION = """
mutation ($id: Int) {
    ToggleFavourite (studioId: $id) {
        studios {
            pageInfo {
                total
            }
        }
    }
}
"""

CHAR_MUTATION = """
mutation ($id: Int) {
    ToggleFavourite (characterId: $id) {
        characters {
            pageInfo {
                total
            }
        }
    }
}
"""

ANILIST_MUTATION = """
mutation ($id: Int, $status: MediaListStatus) {
    SaveMediaListEntry (mediaId: $id, status: $status) {
        media {
            title {
                romaji
            }
        }
    }
}
"""

ANILIST_MUTATION_UP = """
mutation ($id: [Int], $status: MediaListStatus) {
    UpdateMediaListEntries (ids: $id, status: $status) {
        media {
            title {
                romaji
            }
        }
    }
}
"""

ANILIST_MUTATION_DEL = """
mutation ($id: Int) {
    DeleteMediaListEntry (id: $id) {
        deleted
    }
}
"""

AIR_QUERY = """
query ($search: String, $page: Int) {
    Page (perPage: 1, page: $page) {
        pageInfo {
            total
            hasNextPage
        } 
        media (search: $search, type: ANIME) {
            id
            title {
                romaji
                english
            }
            status
            countryOfOrigin
            nextAiringEpisode {
                timeUntilAiring
                episode
            }
            siteUrl
            isFavourite
            isAdult
            mediaListEntry {
                status
                id
            }
        }
    }
}
"""

DES_INFO_QUERY = """
query ($id: Int) {
    Media (id: $id) {
        id
        description (asHtml: false)
    }
}
"""

CHA_INFO_QUERY = """
query ($id: Int, $page: Int) {
    Media (id: $id, type: ANIME) {
        id
        characters (page: $page, perPage: 25, sort: ROLE) {
            pageInfo {
                hasNextPage
                lastPage
                total
            }
            edges {
                node {
        	        name {
          	            full
        	        }
                }
                role
            }
        }
    }
}
"""

REL_INFO_QUERY = """
query ($id: Int) {
    Media (id: $id, type: ANIME) {
        id
        relations {
            edges {
                node {
                    title {
                        romaji
                    }
                    type
                }
                relationType
            }
        }
    }
}
"""

PAGE_QUERY = """
query ($search: String, $page: Int) {
    Page (perPage: 1, page: $page) {
        pageInfo {
            total
            hasNextPage
        }
        media (search: $search, type: ANIME) {
            id
            idMal
            title {
                romaji
                english
                native
            }
            format
            status
            episodes
            duration
            countryOfOrigin
            source (version: 2)
            trailer {
                id
                site
            }
            genres
            tags {
                name
            }
            averageScore
            relations {
                edges {
                    node {
                        title {
                            romaji
                            english
                        }
                        type
                    }
                    relationType
                }
            }
            nextAiringEpisode {
                timeUntilAiring
                episode
            }
            isAdult
            isFavourite
            mediaListEntry {
                status
                score
                id
            }
            siteUrl
        }
    }
}
"""

CHARACTER_QUERY = """
query ($id: Int, $search: String, $page: Int) {
    Page (perPage: 1, page: $page) {
        pageInfo {
            total
            hasNextPage
        }
        characters (id: $id, search: $search) {
            id
            name {
                full
                native
            }
            image {
                large
            }
            media (type: ANIME) {
                edges {
                    node {
                        title {
                            romaji
                        }
                        type
                    }
                    voiceActors (language: JAPANESE) {
                        name {
                            full
         	            }
                        siteUrl
                    }
                }
            }
            isFavourite
            siteUrl
        }
    }
}
"""

MANGA_QUERY = """
query ($search: String, $page: Int) {
    Page (perPage: 1, page: $page) {
        pageInfo {
            total
            hasNextPage
        }
        media (search: $search, type: MANGA) {
            id
            title {
                romaji
                english
                native
            }
            format
            countryOfOrigin
            source (version: 2)
            status
            description(asHtml: true)
            chapters
            isFavourite
            mediaListEntry {
                status
                score
                id
            }
            volumes
            averageScore
            siteUrl
            isAdult
        }
    }
}
"""


DESC_INFO_QUERY = """
query ($id: Int) {
    Character (id: $id) {
        image {
            large
        }
        description(asHtml: false)
    }
}
"""

LS_INFO_QUERY = """
query ($id: Int) {
    Character (id: $id) {
        image {
            large
        }
        media (page: 1, perPage: 25) {
            nodes {
                title {
                    romaji
                    english
                }
                type
            }
        }
    }
}
"""

ACTIVITY_QUERY = """
query ($id: Int) {
    Page (perPage: 12) {
  	    activities (userId: $id, type: MEDIA_LIST, sort: ID_DESC) {
			...kek
  	    }
    }
}
fragment kek on ListActivity {
    type
    media {
        title {
            romaji
        }
        siteUrl
    }
    progress
    status
}
"""

TOP_QUERY = """
query ($gnr: String, $page: Int) {
    Page (perPage: 15, page: $page) {
        pageInfo {
            lastPage
            total
            hasNextPage
        }
        media (genre: $gnr, sort: SCORE_DESC, type: ANIME) {
            title {
                romaji
            }
        }
    }
}
"""

TOPT_QUERY = """
query ($gnr: String, $page: Int) {
    Page (perPage: 15, page: $page) {
        pageInfo {
            lastPage
            total
            hasNextPage
        }
        media (tag: $gnr, sort: SCORE_DESC, type: ANIME) {
            title {
                romaji
            }
        }
    }
}
"""

ALLTOP_QUERY = """
query ($page: Int) {
    Page (perPage: 15, page: $page) {
        pageInfo {
            lastPage
            total
            hasNextPage
        }
        media (sort: SCORE_DESC, type: ANIME) {
            title {
                romaji
            }
        }
    }
}
"""

GET_GENRES = """
query {
    GenreCollection
}
"""

GET_TAGS = """
query{
    MediaTagCollection {
        name
        isAdult
    }
}
"""

RECOMMENDTIONS_QUERY = """
query ($id: Int) {
    Media (id: $id) {
        recommendations (perPage: 25) {
            edges {
                node {
                    mediaRecommendation {
                        title {
                            romaji
                        }
                        id
                        siteUrl
                    }
                }
            }
        }
    }
}
"""

STUDIO_QUERY = """
query ($search: String, $page: Int) {
    Page (page: $page, perPage: 1) {
        pageInfo {
            total
            hasNextPage
        }
  	    studios (search: $search) {
    	    id
    	    name
  	        siteUrl
            isFavourite
  	    }
	}
}
"""

STUDIO_ANI_QUERY = """
query ($id: Int, $page: Int) {
    Studio (id: $id) {
        name
        media (page: $page) {
            pageInfo {
                total
                lastPage
                hasNextPage
            }
            edges {
                node  {
                    title {
                        romaji
                    }
                    seasonYear
                }
            }
        }
    }
}
"""


async def get_studios(qry, page, user, duser=None, auth: bool = False):
    page = int(page)
    vars_ = {"search": STUDIO_DB[qry], "page": int(page)}
    result = await return_json_senpai(STUDIO_QUERY, vars_, auth, user)
    if result["data"]["Page"]["studios"] == []:
        return ["Not Found"]
    data = result["data"]["Page"]["studios"][0]
    isFav = data["isFavourite"]
    msg = (
        f"**{data['name']}**{', ♥️' if isFav is True else ''}"
        + f"\n\n**ID:** {data['id']}\n[Website]({data['siteUrl']})"
    )
    if not duser:
        duser = user
    btns = []
    btns.append(
        [
            InlineKeyboardButton(
                "List Animes",
                callback_data=f"stuani_1_{data['id']}_{page}_{qry}_{auth}_{duser}",
            )
        ]
    )
    if auth:
        btns.append(
            [
                InlineKeyboardButton(
                    "Remove from Favs" if isFav else "Add To Favs",
                    callback_data=f"fav_STUDIO_{data['id']}_{qry}_{page}_{duser}",
                )
            ]
        )
    pi = result["data"]["Page"]["pageInfo"]["hasNextPage"]
    if pi is False:
        if int(page) == 1:
            return msg, btns
        else:
            btns.append(
                [
                    InlineKeyboardButton(
                        "Prev", callback_data=f"pgstudio_{page-1}_{qry}_{auth}_{duser}"
                    )
                ]
            )
    else:
        if int(page) == 1:
            btns.append(
                [
                    InlineKeyboardButton(
                        "Next", callback_data=f"pgstudio_2_{qry}_{auth}_{duser}"
                    )
                ]
            )
        else:
            btns.append(
                [
                    InlineKeyboardButton(
                        "Prev", callback_data=f"pgstudio_{page-1}_{qry}_{auth}_{duser}"
                    ),
                    InlineKeyboardButton(
                        "Next", callback_data=f"pgstudio_{page+1}_{qry}_{auth}_{duser}"
                    ),
                ]
            )
    return msg, InlineKeyboardMarkup(btns)


async def get_studio_animes(id_, page, qry, rp, user, duser=None, auth: bool = False):
    vars_ = {"id": id_, "page": int(page)}
    result = await return_json_senpai(STUDIO_ANI_QUERY, vars_, auth, user)
    data = result["data"]["Studio"]["media"]["edges"]
    if data == []:
        return ["No results found"]
    msg = f"List of animes by {result['data']['Studio']['name']} studio\n"
    for i in data:
        msg += (
            f"\n⚬ `{i['node']['title']['romaji']}`"
            + f" __({i['node']['seasonYear']})__"
        )
    btns = []
    if not duser:
        duser = user
    pi = result["data"]["Studio"]["media"]["pageInfo"]
    if pi["hasNextPage"] is False:
        if int(page) == 1:
            btns.append(
                [
                    InlineKeyboardButton(
                        "Back", callback_data=f"pgstudio_{rp}_{qry}_{auth}_{duser}"
                    )
                ]
            )
            return msg, btns
        else:
            btns.append(
                [
                    InlineKeyboardButton(
                        "Prev",
                        callback_data=f"stuani_{int(page)-1}_{id_}_{rp}_{qry}_{auth}_{duser}",
                    )
                ]
            )
    else:
        if int(page) == 1:
            btns.append(
                [
                    InlineKeyboardButton(
                        "Next",
                        callback_data=f"stuani_2_{id_}_{rp}_{qry}_{auth}_{duser}",
                    )
                ]
            )
        else:
            btns.append(
                [
                    InlineKeyboardButton(
                        "Prev",
                        callback_data=f"stuani_{int(page)-1}_{id_}_{rp}_{qry}_{auth}_{duser}",
                    ),
                    InlineKeyboardButton(
                        "Next",
                        callback_data=f"stuani_{int(page)+1}_{id_}_{rp}_{qry}_{auth}_{duser}",
                    ),
                ]
            )
    btns.append(
        [
            InlineKeyboardButton(
                "Back", callback_data=f"pgstudio_{rp}_{qry}_{auth}_{duser}"
            )
        ]
    )
    return msg, InlineKeyboardMarkup(btns)


async def get_all_tags(text: str = None):
    vars_ = {}
    result = await return_json_senpai(GET_TAGS, vars_, auth=False, user=None)
    msg = "**Tags List:**\n\n`"
    kek = []
    for i in result["data"]["MediaTagCollection"]:
        if text is not None and "nsfw" in text:
            if str(i["isAdult"]) != "False":
                kek.append(i["name"])
        else:
            if str(i["isAdult"]) == "False":
                kek.append(i["name"])
    msg += ", ".join(kek)
    msg += "`"
    return msg


async def get_all_genres():
    vars_ = {}
    result = await return_json_senpai(GET_GENRES, vars_, auth=False)
    msg = "**Genres List:**\n\n"
    for i in result["data"]["GenreCollection"]:
        msg += f"`{i}`\n"
    return msg


async def get_user_activity(id_, user, duser=None):
    vars_ = {"id": id_}
    result = await return_json_senpai(ACTIVITY_QUERY, vars_, auth=True, user=user)
    data = result["data"]["Page"]["activities"]
    msg = ""
    for i in data:
        try:
            name = f"[{i['media']['title']['romaji']}]" + f"({i['media']['siteUrl']})"
            if i["status"] in ["watched episode", "read chapter"]:
                msg += (
                    f"⚬ {str(i['status']).capitalize()} "
                    + f"{i['progress']} of {name}\n"
                )
            else:
                progress = i["progress"]
                of = "of"
                if i["status"] == "dropped":
                    of = "at"
                msg += (
                    f"⚬ {str(i['status']).capitalize()}"
                    + f"{f'{progress} {of} ' if progress is not None else ' '}"
                    + f"{name}\n"
                )
        except KeyError:
            pass
    if duser is None:
        duser = user
    btn = [[InlineKeyboardButton("Back", callback_data=f"getusrbc_{duser}")]]
    return [
        f"https://img.anili.st/user/{id_}?a={time.time()}",
        msg,
        InlineKeyboardMarkup(btn),
    ]


async def get_recommendations(id_):
    vars_ = {"id": int(id_)}
    result = await return_json_senpai(RECOMMENDTIONS_QUERY, vars_)
    data = result["data"]["Media"]["recommendations"]["edges"]
    rc_ls = []
    for i in data:
        ii = i["node"]["mediaRecommendation"]
        rc_ls.append([ii["title"]["romaji"], ii["id"], ii["siteUrl"]])
    if rc_ls == []:
        return "No Recommendations available related to given anime!!!"
    outstr = "Recommended animes:\n\n"
    for i in rc_ls:
        outstr += (
            f"**{i[0]}**\n ➥[Synopsis]"
            + f"(https://t.me/{BOT_USERNAME}?astart=anime_{i[1]})"
            + f"\n ➥[Official Site]({i[2]})\n\n"
        )
    return outstr


async def get_top_animes(gnr: str, page, user):
    vars_ = {"gnr": gnr.lower(), "page": int(page)}
    query = TOP_QUERY
    msg = f"Top animes for genre `{gnr.capitalize()}`:\n\n"
    if gnr == "None":
        query = ALLTOP_QUERY
        vars_ = {"page": int(page)}
        msg = f"Top animes:\n\n"
    nsfw = False
    result = await return_json_senpai(query, vars_, auth=False, user=user)
    if len(result["data"]["Page"]["media"]) == 0:
        query = TOPT_QUERY
        msg = f"Top animes for tag `{gnr.capitalize()}`:\n\n"
        result = await return_json_senpai(query, vars_, auth=False, user=user)
        if len(result["data"]["Page"]["media"]) == 0:
            return [f"No results Found"]
        nsls = await get_all_tags("nsfw")
        nsfw = True if gnr.lower() in nsls.lower() else False
    data = result["data"]["Page"]
    for i in data["media"]:
        msg += f"⚬ `{i['title']['romaji']}`\n"
    msg += f"\nTotal available animes: `{data['pageInfo']['total']}`"
    btn = []
    if int(page) == 1:
        if int(data["pageInfo"]["lastPage"]) != 1:
            btn.append(
                [
                    InlineKeyboardButton(
                        "Next", callback_data=f"topanimu_{gnr}_{int(page)+1}_{user}"
                    )
                ]
            )
    elif int(page) == int(data["pageInfo"]["lastPage"]):
        btn.append(
            [
                InlineKeyboardButton(
                    "Prev", callback_data=f"topanimu_{gnr}_{int(page)-1}_{user}"
                )
            ]
        )
    else:
        btn.append(
            [
                InlineKeyboardButton(
                    "Prev", callback_data=f"topanimu_{gnr}_{int(page)-1}_{user}"
                ),
                InlineKeyboardButton(
                    "Next", callback_data=f"topanimu_{gnr}_{int(page)+1}_{user}"
                ),
            ]
        )
    return [msg, nsfw], InlineKeyboardMarkup(btn) if len(btn) != 0 else ""


async def get_user_favourites(id_, user, req, page, sighs, duser=None):
    vars_ = {"id": int(id_), "page": int(page)}
    result = await return_json_senpai(
        (
            FAV_ANI_QUERY
            if req == "ANIME"
            else FAV_CHAR_QUERY if req == "CHAR" else FAV_MANGA_QUERY
        ),
        vars_,
        auth=True,
        user=int(user),
    )
    data = result["data"]["User"]["favourites"][
        "anime" if req == "ANIME" else "characters" if req == "CHAR" else "manga"
    ]
    msg = (
        "Favourite Animes:\n\n"
        if req == "ANIME"
        else "Favourite Characters:\n\n" if req == "CHAR" else "Favourite Manga:\n\n"
    )
    for i in data["edges"]:
        node_name = (
            i["node"]["title"]["romaji"] if req != "CHAR" else i["node"]["name"]["full"]
        )
        msg += f"⚬ [{node_name}]({i['node']['siteUrl']})\n"
    btn = []
    if duser is None:
        duser = user
    if int(page) == 1:
        if int(data["pageInfo"]["lastPage"]) != 1:
            btn.append(
                [
                    InlineKeyboardButton(
                        "Next",
                        callback_data=(
                            f"myfavqry_{req}_{id_}_{str(int(page)+1)}"
                            + f"_{sighs}_{duser}"
                        ),
                    )
                ]
            )
    elif int(page) == int(data["pageInfo"]["lastPage"]):
        btn.append(
            [
                InlineKeyboardButton(
                    "Prev",
                    callback_data=(
                        f"myfavqry_{req}_{id_}_{str(int(page)-1)}_{sighs}_{duser}"
                    ),
                )
            ]
        )
    else:
        btn.append(
            [
                InlineKeyboardButton(
                    "Prev",
                    callback_data=(
                        f"myfavqry_{req}_{id_}_{str(int(page)-1)}_{sighs}_{duser}"
                    ),
                ),
                InlineKeyboardButton(
                    "Next",
                    callback_data=(
                        f"myfavqry_{req}_{id_}_{str(int(page)+1)}_{sighs}_{duser}"
                    ),
                ),
            ]
        )
    btn.append(
        [InlineKeyboardButton("Back", callback_data=f"myfavs_{id_}_{sighs}_{user}")]
    )
    return [
        f"https://img.anili.st/user/{id_}?a=({time.time()})",
        msg,
        InlineKeyboardMarkup(btn),
    ]


async def get_featured_in_lists(
    idm, req, auth: bool = False, user: int = None, page: int = 0
):
    vars_ = {"id": int(idm)}
    result = await return_json_senpai(LS_INFO_QUERY, vars_, auth=auth, user=user)
    data = result["data"]["Character"]["media"]["nodes"]
    if req == "ANI":
        out = "ANIMES:\n\n"
        out_ = []
        for ani in data:
            k = ani["title"]["english"] or ani["title"]["romaji"]
            kk = ani["type"]
            if kk == "ANIME":
                out_.append(f"• __{k}__\n")
    else:
        out = "MANGAS:\n\n"
        out_ = []
        for ani in data:
            k = ani["title"]["english"] or ani["title"]["romaji"]
            kk = ani["type"]
            if kk == "MANGA":
                out_.append(f"• __{k}__\n")
    total = len(out_)
    for _ in range(15 * page):
        out_.pop(0)
    out_ = "".join(out_[:15])
    return ([out + out_, total] if len(out_) != 0 else False), result["data"][
        "Character"
    ]["image"]["large"]


async def get_additional_info(
    idm, ctgry, req=None, auth: bool = False, user: int = None, page: int = 0
):
    vars_ = {"id": int(idm)}
    if req == "char":
        vars_["page"] = page
    result = await return_json_senpai(
        (
            (
                DES_INFO_QUERY
                if req == "desc"
                else CHA_INFO_QUERY if req == "char" else REL_INFO_QUERY
            )
            if ctgry == "ANI"
            else DESC_INFO_QUERY
        ),
        vars_,
    )
    data = result["data"]["Media"] if ctgry == "ANI" else result["data"]["Character"]
    pic = f"https://img.anili.st/media/{idm}"
    if req == "desc":
        synopsis = data.get("description")
        if os.environ.get("PREFERRED_LANGUAGE"):
            synopsis = tr.translate(
                synopsis, lang_tgt=os.environ.get("PREFERRED_LANGUAGE")
            )
        return (pic if ctgry == "ANI" else data["image"]["large"]), synopsis
    elif req == "char":
        charlist = []
        for char in data["characters"]["edges"]:
            charlist.append(f"• `{char['node']['name']['full']}` ({char['role']})")
        chrctrs = ("\n").join(charlist)
        charls = f"{chrctrs}" if len(charlist) != 0 else ""
        return pic, charls, data["characters"]["pageInfo"]
    else:
        prqlsql = data.get("relations").get("edges")
        ps = ""
        for i in prqlsql:
            ps += (
                f'• {i["node"]["title"]["romaji"]} '
                + f'({i["node"]["type"]}) `{i["relationType"]}`\n'
            )
        return pic, ps


async def get_anime(vars_, auth: bool = False, user: int = None, cid: int = None):
    result = await return_json_senpai(ANIME_QUERY, vars_, auth=auth, user=user)

    error = result.get("errors")
    if error:
        error_sts = error[0].get("message")
        return [f"[{error_sts}]"]

    data = result["data"]["Media"]

    # Data of all fields in returned json
    # pylint: disable=possibly-unused-variable
    idm = data.get("id")
    idmal = data.get("idMal")
    romaji = data["title"]["romaji"]
    english = data["title"]["english"]
    native = data["title"]["native"]
    formats = data.get("format")
    status = data.get("status")
    episodes = data.get("episodes")
    duration = data.get("duration")
    country = data.get("countryOfOrigin")
    c_flag = cflag(country)
    source = data.get("source")
    prqlsql = data.get("relations").get("edges")
    adult = data.get("isAdult")
    url = data.get("siteUrl")
    trailer_link = "N/A"
    gnrs = ", ".join(data["genres"])
    score = data["averageScore"]
    bl, cs = await uidata(cid)
    text = await get_ui_text(cs)
    psrc, ptype = text[0], text[1]
    avscd = f"\n{bl}**{text[2]}:** `{score}%` 🌟" if score is not None else ""
    tags = []
    for i in data["tags"]:
        tags.append(i["name"])
    tags_ = f"\n{bl}**{text[8]}:** `{', '.join(tags[:5])}`" if tags != [] else ""
    bot = BOT_USERNAME.replace("@", "")
    gnrs_ = ""
    if len(gnrs) != 0:
        gnrs_ = f"\n{bl}**{text[7]}:** `{gnrs}`"
    isfav = data.get("isFavourite")
    fav = ", in Favourites" if isfav is True else ""
    user_data = ""
    in_ls = False
    in_ls_id = ""
    if auth is True:
        in_list = data.get("mediaListEntry")
        if in_list is not None:
            in_ls = True
            in_ls_id = in_list["id"]
            in_ls_stts = in_list["status"]
            in_ls_score = (
                f" and scored {in_list['score']}" if in_list["score"] != 0 else ""
            )
            user_data = f"\n{bl}**{text[4]}:** `{in_ls_stts}{fav}{in_ls_score}`"
    if data["title"]["english"] is not None:
        name = f"""[{c_flag}]**{romaji}** | {native}"""
    else:
        name = f"""[{c_flag}]**{romaji}** | {native}"""
    prql, prql_id, sql, sql_id = "", "None", "", "None"
    for i in prqlsql:
        if i["relationType"] == "PREQUEL" and i["node"]["type"] == "ANIME":
            pname = (
                i["node"]["title"]["english"]
                if i["node"]["title"]["english"] is not None
                else i["node"]["title"]["romaji"]
            )
            prql += f"**{text[10]}:** `{pname}`\n"
            prql_id = i["node"]["id"]
            break
    for i in prqlsql:
        if i["relationType"] == "SEQUEL" and i["node"]["type"] == "ANIME":
            sname = (
                i["node"]["title"]["english"]
                if i["node"]["title"]["english"] is not None
                else i["node"]["title"]["romaji"]
            )
            sql += f"**{text[9]}:** `{sname}`\n"
            sql_id = i["node"]["id"]
            break
    additional = f"{prql}{sql}"
    surl = f"https://t.me/{bot}/?astart=des_ANI_{idm}_desc"
    dura = f"\n{bl}**{text[3]}:** `{duration} min/ep`" if duration is not None else ""
    air_on = None
    if data["nextAiringEpisode"]:
        nextAir = data["nextAiringEpisode"]["timeUntilAiring"]
        air_on = make_it_rw(nextAir * 1000)
        eps = data["nextAiringEpisode"]["episode"]
        th = pos_no(str(eps))
        air_on += f" | {eps}{th} eps"
    if air_on is None:
        eps_ = f"` | `{episodes} eps" if episodes is not None else ""
        status_air = f"{bl}**{text[6]}:** `{status}{eps_}`"
    else:
        status_air = f"{bl}**{text[6]}:** `{status}`\n{bl}**{text[11]}:** `{air_on}`"
    if data["trailer"] and data["trailer"]["site"] == "youtube":
        trailer_link = f"<a href='https://youtu.be/{data['trailer']['id']}'>Trailer</a>"
    title_img = f"https://img.anili.st/media/{idm}"
    try:
        finals_ = ANIME_TEMPLATE.format(**locals())
    except KeyError as kys:
        return [f"{kys}"]
    return (
        title_img,
        finals_,
        [idm, in_ls, in_ls_id, isfav, str(adult)],
        prql_id,
        sql_id,
    )


async def get_anilist(qdb, page, auth: bool = False, user: int = None, cid: int = None):
    vars_ = {"search": ANIME_DB[qdb], "page": page}
    result = await return_json_senpai(PAGE_QUERY, vars_, auth=auth, user=user)

    if len(result["data"]["Page"]["media"]) == 0:
        return [f"No results Found"]

    data = result["data"]["Page"]["media"][0]
    # Data of all fields in returned json
    # pylint: disable=possibly-unused-variable
    idm = data.get("id")
    bot = BOT_USERNAME.replace("@", "")
    idmal = data.get("idMal")
    romaji = data["title"]["romaji"]
    english = data["title"]["english"]
    native = data["title"]["native"]
    formats = data.get("format")
    status = data.get("status")
    episodes = data.get("episodes")
    duration = data.get("duration")
    country = data.get("countryOfOrigin")
    c_flag = cflag(country)
    source = data.get("source")
    prqlsql = data.get("relations").get("edges")
    adult = data.get("isAdult")
    trailer_link = "N/A"
    isfav = data.get("isFavourite")
    gnrs = ", ".join(data["genres"])
    gnrs_ = ""
    bl, cs = await uidata(cid)
    text = await get_ui_text(cs)
    psrc, ptype = text[0], text[1]
    if len(gnrs) != 0:
        gnrs_ = f"\n{bl}**{text[7]}:** `{gnrs}`"
    fav = ", in Favourites" if isfav is True else ""
    score = data["averageScore"]
    avscd = f"\n{bl}**{text[2]}:** `{score}%` 🌟" if score is not None else ""
    tags = []
    for i in data["tags"]:
        tags.append(i["name"])
    tags_ = f"\n{bl}**{text[8]}:** `{', '.join(tags[:5])}`" if tags != [] else ""
    in_ls = False
    in_ls_id = ""
    user_data = ""
    if auth is True:
        in_list = data.get("mediaListEntry")
        if in_list is not None:
            in_ls = True
            in_ls_id = in_list["id"]
            in_ls_stts = in_list["status"]
            in_ls_score = (
                f" and scored {in_list['score']}" if in_list["score"] != 0 else ""
            )
            user_data = f"\n{bl}**{text[4]}:** `{in_ls_stts}{fav}{in_ls_score}`"
    if data["title"]["english"] is not None:
        name = f"[{c_flag}]**{english}** (`{native}`)"
    else:
        name = f"[{c_flag}]**{romaji}** (`{native}`)"
    prql, sql = "", ""
    for i in prqlsql:
        if i["relationType"] == "PREQUEL" and i["node"]["type"] == "ANIME":
            pname = (
                i["node"]["title"]["english"]
                if i["node"]["title"]["english"] is not None
                else i["node"]["title"]["romaji"]
            )
            prql += f"**{text[10]}:** `{pname}`\n"
            break
    for i in prqlsql:
        if i["relationType"] == "SEQUEL" and i["node"]["type"] == "ANIME":
            sname = (
                i["node"]["title"]["english"]
                if i["node"]["title"]["english"] is not None
                else i["node"]["title"]["romaji"]
            )
            sql += f"**{text[9]}:** `{sname}`\n"
            break
    additional = f"{prql}{sql}"
    additional.replace("-", "")
    dura = f"\n{bl}**{text[3]}:** `{duration} min/ep`" if duration is not None else ""
    air_on = None
    if data["nextAiringEpisode"]:
        nextAir = data["nextAiringEpisode"]["timeUntilAiring"]
        air_on = make_it_rw(nextAir * 1000)
        eps = data["nextAiringEpisode"]["episode"]
        th = pos_no(str(eps))
        air_on += f" | {eps}{th} eps"
    if air_on is None:
        eps_ = f"` | `{episodes} eps" if episodes is not None else ""
        status_air = f"{bl}**{text[6]}:** `{status}{eps_}`"
    else:
        status_air = f"{bl}**{text[6]}:** `{status}`\n{bl}**{text[11]}:** `{air_on}`"
    if data["trailer"] and data["trailer"]["site"] == "youtube":
        trailer_link = f"<a href='https://youtu.be/{data['trailer']['id']}'>Trailer</a>"
    url = data.get("siteUrl")
    title_img = f"https://img.anili.st/media/{idm}"
    surl = f"https://t.me/{bot}/?astart=des_ANI_{idm}_desc"
    hasNextPage = result["data"]["Page"]["pageInfo"]["hasNextPage"]
    try:
        finals_ = ANIME_TEMPLATE.format(**locals())
    except KeyError as kys:
        return [f"{kys}"]
    return title_img, [finals_, hasNextPage], [idm, in_ls, in_ls_id, isfav, str(adult)]


async def get_character(query, page, auth: bool = False, user: int = None):
    var = {"search": CHAR_DB[query], "page": int(page)}
    result = await return_json_senpai(CHARACTER_QUERY, var, auth=auth, user=user)
    if len(result["data"]["Page"]["characters"]) == 0:
        return [f"No results Found"]
    data = result["data"]["Page"]["characters"][0]
    # Character Data
    id_ = data["id"]
    name = data["name"]["full"]
    native = data["name"]["native"]
    img = data["image"]["large"]
    site_url = data["siteUrl"]
    isfav = data.get("isFavourite")
    va = []
    for i in data["media"]["edges"]:
        for ii in i["voiceActors"]:
            if f"[{ii['name']['full']}]({ii['siteUrl']})" not in va:
                va.append(f"[{ii['name']['full']}]({ii['siteUrl']})")
    lva = None
    if len(va) > 1:
        lva = va.pop()
    sva = (
        f"\n**Voice Actors:** {', '.join(va)}"
        + f"{' and '+lva if lva is not None else ''}\n"
        if va != []
        else ""
    )
    cap_text = f"""
__{native}__
(`{name}`)
**ID:** {id_}
{sva}
<a href='{site_url}'>Visit Website</a>"""
    hasNextPage = result["data"]["Page"]["pageInfo"]["hasNextPage"]
    return img, [cap_text, hasNextPage], [id_, isfav]


async def browse_(qry: str):
    s, y = season_()
    sort = "POPULARITY_DESC"
    if qry == "upcoming":
        s, y = season_(True)
    if qry == "trending":
        sort = "TRENDING_DESC"
    vars_ = {"s": s, "y": y, "sort": sort}
    result = await return_json_senpai(BROWSE_QUERY, vars_)
    data = result["data"]["Page"]["media"]
    ls = []
    for i in data:
        if i["format"] in ["TV", "MOVIE", "ONA"]:
            ls.append("• `" + i["title"]["romaji"] + "`")
    out = f"{qry.capitalize()} animes in {s} {y}:\n\n"
    return out + "\n".join(ls[:20])


async def get_manga(qdb, page, auth: bool = False, user: int = None, cid: int = None):
    vars_ = {"search": MANGA_DB[qdb], "asHtml": True, "page": page}
    result = await return_json_senpai(MANGA_QUERY, vars_, auth=auth, user=user)
    if len(result["data"]["Page"]["media"]) == 0:
        return [f"No results Found"]
    data = result["data"]["Page"]["media"][0]

    # Data of all fields in returned json
    # pylint: disable=possibly-unused-variable
    idm = data.get("id")
    romaji = data["title"]["romaji"]
    english = data["title"]["english"]
    native = data["title"]["native"]
    status = data.get("status")
    synopsis = data.get("description")
    description = synopsis[:500]
    description_s = ""
    if len(synopsis) > 500:
        description += f"..."
        description_s = (
            f"[Click for more info](https://t.me/{BOT_USERNAME}"
            + f"/?astart=des_ANI_{idm}_desc)"
        )
    volumes = data.get("volumes")
    chapters = data.get("chapters")
    score = data.get("averageScore")
    url = data.get("siteUrl")
    format_ = data.get("format")
    country = data.get("countryOfOrigin")
    source = data.get("source")
    c_flag = cflag(country)
    isfav = data.get("isFavourite")
    adult = data.get("isAdult")
    fav = ", in Favourites" if isfav is True else ""
    in_ls = False
    in_ls_id = ""
    bl, cs = await uidata(cid)
    text = await get_ui_text(cs)
    user_data = ""
    if auth is True:
        in_list = data.get("mediaListEntry")
        if in_list is not None:
            in_ls = True
            in_ls_id = in_list["id"]
            in_ls_stts = in_list["status"]
            in_ls_score = (
                f" and scored {in_list['score']}" if in_list["score"] != 0 else ""
            )
            user_data = f"{bl}**{text[4]}:** `{in_ls_stts}{fav}{in_ls_score}`\n"
    name = f"""[{c_flag}]**{romaji}**
        __{english}__
        {native}"""
    if english is None:
        name = f"""[{c_flag}]**{romaji}**
        {native}"""
    finals_ = f"{name}\n\n"
    finals_ += f"{bl}**ID:** `{idm}`\n"
    finals_ += f"{bl}**{text[6]}:** `{status}`\n"
    finals_ += f"{bl}**{text[13]}:** `{volumes}`\n"
    finals_ += f"{bl}**{text[14]}:** `{chapters}`\n"
    finals_ += f"{bl}**{text[2]}:** `{score}`\n"
    finals_ += f"{bl}**{text[1]}:** `{format_}`\n"
    finals_ += f"{bl}**{text[0]}:** `{source}`\n"
    finals_ += user_data
    if os.environ.get("PREFERRED_LANGUAGE"):
        description = tr.translate(
            description, lang_tgt=os.environ.get("PREFERRED_LANGUAGE")
        )
    findesc = "" if description == "" else f"`{description}`"
    finals_ += f"\n**{text[12]}**: {findesc}\n\n{description_s}"
    pic = f"https://img.anili.st/media/{idm}"
    return (
        pic,
        [finals_, result["data"]["Page"]["pageInfo"]["hasNextPage"], url],
        [idm, in_ls, in_ls_id, isfav, str(adult)],
    )


async def get_airing(qry, ind: int, auth: bool = False, user: int = None):
    vars_ = {"search": AIRING_DB[qry], "page": int(ind)}
    result = await return_json_senpai(AIR_QUERY, vars_, auth=auth, user=user)
    error = result.get("errors")
    if error:
        error_sts = error[0].get("message")
        return [f"{error_sts}"]
    try:
        data = result["data"]["Page"]["media"][0]
    except IndexError:
        return ["No results Found"]
    # Airing Details
    mid = data.get("id")
    romaji = data["title"]["romaji"]
    english = data["title"]["english"]
    status = data.get("status")
    country = data.get("countryOfOrigin")
    c_flag = cflag(country)
    coverImg = f"https://img.anili.st/media/{mid}"
    isfav = data.get("isFavourite")
    adult = data.get("isAdult")
    in_ls = False
    in_ls_id = ""
    user_data = ""
    if auth is True:
        in_list = data.get("mediaListEntry")
        if in_list is not None:
            in_ls = True
            in_ls_id = in_list["id"]
            in_ls_stts = in_list["status"]
            user_data = f"**USER DATA:** `{in_ls_stts}`\n"
    air_on = None
    if data["nextAiringEpisode"]:
        nextAir = data["nextAiringEpisode"]["timeUntilAiring"]
        episode = data["nextAiringEpisode"]["episode"]
        th = pos_no(episode)
        air_on = make_it_rw(nextAir * 1000)
    title_ = english or romaji
    out = f"[{c_flag}] **{title_}**"
    out += f"\n\n**ID:** `{mid}`"
    out += f"\n**Status:** `{status}`\n"
    out += user_data
    if air_on:
        out += f"Airing Episode `{episode}{th}` in `{air_on}`"
    site = data["siteUrl"]
    return (
        [coverImg, out],
        [site, result["data"]["Page"]["pageInfo"]["hasNextPage"]],
        [mid, in_ls, in_ls_id, isfav, str(adult)],
    )


async def toggle_favourites(id_: int, media: str, user: int):
    vars_ = {"id": int(id_)}
    query = (
        ANIME_MUTATION
        if media == "ANIME" or media == "AIRING"
        else (
            CHAR_MUTATION
            if media == "CHARACTER"
            else MANGA_MUTATION if media == "MANGA" else STUDIO_MUTATION
        )
    )
    k = await return_json_senpai(query=query, vars_=vars_, auth=True, user=int(user))
    try:
        kek = k["data"]["ToggleFavourite"]
        return "ok"
    except KeyError:
        return "failed"


async def get_user(vars_, req, user, display_user=None):
    query = USER_QRY if "user" in req else VIEWER_QRY
    k = await return_json_senpai(
        query=query, vars_=vars_, auth=False if "user" in req else True, user=int(user)
    )
    error = k.get("errors")
    if error:
        error_sts = error[0].get("message")
        return [f"{error_sts}"]

    data = k["data"]["User" if "user" in req else "Viewer"]
    anime = data["statistics"]["anime"]
    manga = data["statistics"]["manga"]
    stats = f"""
**Anime Stats**:

Total Anime Watched: `{anime['count']}`
Total Episode Watched: `{anime['episodesWatched']}`
Total Time Spent: `{anime['minutesWatched']}`
Average Score: `{anime['meanScore']}`

**Manga Stats**:

Total Manga Read: `{manga['count']}`
Total Chapters Read: `{manga['chaptersRead']}`
Total Volumes Read: `{manga['volumesRead']}`
Average Score: `{manga['meanScore']}`
"""
    btn = []
    if not "user" in req:
        btn.append(
            [
                InlineKeyboardButton(
                    "Favourites",
                    callback_data=f"myfavs_{data['id']}_yes_{display_user}",
                ),
                InlineKeyboardButton(
                    "Activity", callback_data=f"myacc_{data['id']}_{display_user}"
                ),
            ]
        )
    btn.append([InlineKeyboardButton("Profile", url=str(data["siteUrl"]))])
    return [
        f'https://img.anili.st/user/{data["id"]}?a={time.time()}',
        stats,
        InlineKeyboardMarkup(btn),
    ]


async def update_anilist(id_, req, user, eid: int = None, status: str = None):
    vars_ = {"id": int(id_), "status": status}
    if req == "lsus":
        vars_ = {"id": int(eid), "status": status}
    if req == "dlt":
        vars_ = {"id": int(eid)}
    k = await return_json_senpai(
        query=(
            ANILIST_MUTATION
            if req == "lsas"
            else ANILIST_MUTATION_UP if req == "lsus" else ANILIST_MUTATION_DEL
        ),
        vars_=vars_,
        auth=True,
        user=int(user),
    )
    try:
        (
            k["data"]["SaveMediaListEntry"]
            if req == "lsas"
            else (
                k["data"]["UpdateMediaListEntries"]
                if req == "lsus"
                else k["data"]["DeleteMediaListEntry"]
            )
        )
        return "ok"
    except KeyError:
        return "failed"


async def check_if_adult(id_):
    vars_ = {"id": int(id_)}
    k = await return_json_senpai(query=ISADULT, vars_=vars_, auth=False)
    if str(k["data"]["Media"]["isAdult"]) == "True":
        return "True"
    else:
        return "False"


####       END        ####

#### Jikanpy part ####


async def get_scheduled(x: int = 9):
    base_url = "https://api.jikan.moe/v4/schedules/"
    day = str(day_(x if x != 9 else datetime.now().weekday())).lower()
    out = f"Scheduled animes for {day.capitalize()}\n\n"
    data = requests.get(base_url + day).json()
    sched_ls = data["data"]
    for i in sched_ls:
        try:
            title = i["titles"][0]["title"]
        except IndexError:
            title = i["title"]
        out += f"• `{title}`\n"
    return out, x if x != 9 else datetime.now().weekday()


####     END      ####

#### chiaki part ####


def get_wols(x: str):
    data = requests.get(f"https://chiaki.vercel.app/search2?query={x}").json()
    ls = []
    for i in data:
        sls = [data[i], i]
        ls.append(sls)
    return ls


def get_wo(x: int, page: int):
    data = requests.get(f"https://chiaki.vercel.app/get2?group_id={x}").json()
    msg = "Watch order for the given query is:\n\n"
    out = []
    for i in data:
        out.append(f"{i['index']}. `{i['name']}`\n")
    total = len(out)
    for _ in range(50 * page):
        out.pop(0)
    out_ = "".join(out[:50])
    return msg + out_, total


####     END     ####

##### Anime Fillers Part #####


def search_filler(query):
    html = requests.get("https://www.animefillerlist.com/shows").text
    soup = BeautifulSoup(html, "html.parser")
    div = soup.findAll("div", attrs={"class": "Group"})
    index = {}
    for i in div:
        li = i.findAll("li")
        for jk in li:
            yum = jk.a["href"].split("/")[-1]
            cum = jk.text
            index[cum] = yum
    ret = {}
    keys = list(index.keys())
    for i in range(len(keys)):
        if query.lower() in keys[i].lower():
            ret[keys[i]] = index[keys[i]]
    return ret


def parse_filler(filler_id):
    url = "https://www.animefillerlist.com/shows/" + filler_id
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")
    div = soup.find("div", attrs={"id": "Condensed"})
    all_ep = div.find_all("span", attrs={"class": "Episodes"})
    if len(all_ep) == 1:
        ttl_ep = all_ep[0].findAll("a")
        total_ep = []
        mix_ep = None
        filler_ep = None
        ac_ep = None
        for tol in ttl_ep:
            total_ep.append(tol.text)
        dict_ = {
            "filler_id": filler_id,
            "total_ep": ", ".join(total_ep),
            "mixed_ep": mix_ep,
            "filler_ep": filler_ep,
            "ac_ep": ac_ep,
        }
        return dict_
    if len(all_ep) == 2:
        ttl_ep = all_ep[0].findAll("a")
        fl_ep = all_ep[1].findAll("a")
        total_ep = []
        mix_ep = None
        ac_ep = None
        filler_ep = []
        for tol in ttl_ep:
            total_ep.append(tol.text)
        for fol in fl_ep:
            filler_ep.append(fol.text)
        dict_ = {
            "filler_id": filler_id,
            "total_ep": ", ".join(total_ep),
            "mixed_ep": mix_ep,
            "filler_ep": ", ".join(filler_ep),
            "ac_ep": ac_ep,
        }
        return dict_
    if len(all_ep) == 3:
        ttl_ep = all_ep[0].findAll("a")
        mxl_ep = all_ep[1].findAll("a")
        fl_ep = all_ep[2].findAll("a")
        total_ep = []
        mix_ep = []
        filler_ep = []
        ac_ep = None
        for tol in ttl_ep:
            total_ep.append(tol.text)
        for fol in fl_ep:
            filler_ep.append(fol.text)
        for mol in mxl_ep:
            mix_ep.append(mol.text)
        dict_ = {
            "filler_id": filler_id,
            "total_ep": ", ".join(total_ep),
            "mixed_ep": ", ".join(mix_ep),
            "filler_ep": ", ".join(filler_ep),
            "ac_ep": ac_ep,
        }
        return dict_
    if len(all_ep) == 4:
        ttl_ep = all_ep[0].findAll("a")
        mxl_ep = all_ep[1].findAll("a")
        fl_ep = all_ep[2].findAll("a")
        al_ep = all_ep[3].findAll("a")
        total_ep = []
        mix_ep = []
        filler_ep = []
        ac_ep = []
        for tol in ttl_ep:
            total_ep.append(tol.text)
        for fol in fl_ep:
            filler_ep.append(fol.text)
        for mol in mxl_ep:
            mix_ep.append(mol.text)
        for aol in al_ep:
            ac_ep.append(aol.text)
        dict_ = {
            "filler_id": filler_id,
            "total_ep": ", ".join(total_ep),
            "mixed_ep": ", ".join(mix_ep),
            "filler_ep": ", ".join(filler_ep),
            "ac_ep": ", ".join(ac_ep),
        }
        return dict_


@app.on_message(
    filters.command(["anime", f"anime{BOT_USERNAME}"], prefixes=PREFIX_HANDLER)
)
@control_user
async def anime_cmd(client: Client, message: Message, mdata: dict):
    """Search Anime Info"""
    text = mdata["text"].split(" ", 1)
    gid = mdata["chat"]["id"]
    try:
        user = mdata["from_user"]["id"]
        auser = mdata["from_user"]["id"]
    except KeyError:
        user = mdata["sender_chat"]["id"]
        ufc = await gcc(user)
        if ufc is not None:
            auser = ufc
        else:
            auser = user
    find_gc = await DC.find_one({"_id": gid})
    if find_gc is not None and "anime" in find_gc["cmd_list"].split():
        return
    if len(text) == 1:
        k = await message.reply_text(
            """Please give a query to search about

example: /anime Sword Art Online"""
        )
        await asyncio.sleep(5)
        return await k.delete()
    query = text[1]
    auth = False
    vars_ = {"search": query}
    if query.isdigit():
        vars_ = {"id": int(query)}
    if await AUTH_USERS.find_one({"id": auser}):
        auth = True
    result = await get_anime(
        vars_, user=auser, auth=auth, cid=gid if gid != user else None
    )
    if len(result) != 1:
        title_img, finals_ = result[0], result[1]
    else:
        k = await message.reply_text(result[0])
        await asyncio.sleep(5)
        return await k.delete()
    buttons = get_btns("ANIME", result=result, user=user, auth=auth)
    if await SFW_GRPS.find_one({"id": gid}) and result[2].pop() == "True":
        await client.send_photo(
            gid,
            no_pic[random.randint(0, 4)],
            caption="This anime is marked 18+ and not allowed in this group",
        )
        return
    try:
        await client.send_photo(gid, title_img, caption=finals_, reply_markup=buttons)
    except (WebpageMediaEmpty, WebpageCurlFailed):
        await clog("Mikobot", title_img, "LINK", msg=message)
        await client.send_photo(gid, failed_pic, caption=finals_, reply_markup=buttons)


@app.on_message(
    filters.command(["manga", f"manga{BOT_USERNAME}"], prefixes=PREFIX_HANDLER)
)
@control_user
async def manga_cmd(client: Client, message: Message, mdata: dict):
    """Search Manga Info"""
    text = mdata["text"].split(" ", 1)
    gid = mdata["chat"]["id"]
    try:
        user = mdata["from_user"]["id"]
        auser = mdata["from_user"]["id"]
    except KeyError:
        user = mdata["sender_chat"]["id"]
        ufc = await gcc(user)
        if ufc is not None:
            auser = ufc
        else:
            auser = user
    find_gc = await DC.find_one({"_id": gid})
    if find_gc is not None and "manga" in find_gc["cmd_list"].split():
        return
    if len(text) == 1:
        k = await message.reply_text(
            """Please give a query to search about

example: /manga Sword Art Online"""
        )
        await asyncio.sleep(5)
        return await k.delete()
    query = text[1]
    qdb = rand_key()
    MANGA_DB[qdb] = query
    auth = False
    if await AUTH_USERS.find_one({"id": auser}):
        auth = True
    result = await get_manga(
        qdb, 1, auth=auth, user=auser, cid=gid if gid != user else None
    )
    if len(result) == 1:
        k = await message.reply_text(result[0])
        await asyncio.sleep(5)
        return await k.delete()
    pic, finals_ = result[0], result[1][0]
    buttons = get_btns(
        "MANGA", lsqry=qdb, lspage=1, user=user, result=result, auth=auth
    )
    if await SFW_GRPS.find_one({"id": gid}) and result[2].pop() == "True":
        buttons = get_btns(
            "MANGA",
            lsqry=qdb,
            lspage=1,
            user=user,
            result=result,
            auth=auth,
            sfw="True",
        )
        await client.send_photo(
            gid,
            no_pic[random.randint(0, 4)],
            caption="This manga is marked 18+ and not allowed in this group",
            reply_markup=buttons,
        )
        return
    try:
        await client.send_photo(gid, pic, caption=finals_, reply_markup=buttons)
    except (WebpageMediaEmpty, WebpageCurlFailed):
        await clog("Mikobot", pic, "LINK", msg=message)
        await client.send_photo(gid, failed_pic, caption=finals_, reply_markup=buttons)


@app.on_message(
    filters.command(["character", f"character{BOT_USERNAME}"], prefixes=PREFIX_HANDLER)
)
@control_user
async def character_cmd(client: Client, message: Message, mdata: dict):
    """Get Info about a Character"""
    text = mdata["text"].split(" ", 1)
    gid = mdata["chat"]["id"]
    try:
        user = mdata["from_user"]["id"]
        auser = mdata["from_user"]["id"]
    except KeyError:
        user = mdata["sender_chat"]["id"]
        ufc = await gcc(user)
        if ufc is not None:
            auser = ufc
        else:
            auser = user
    find_gc = await DC.find_one({"_id": gid})
    if find_gc is not None and "character" in find_gc["cmd_list"].split():
        return
    if len(text) == 1:
        k = await message.reply_text(
            "Please give a query to search about\nexample: /character Luffy"
        )
        await asyncio.sleep(5)
        return await k.delete()
    query = text[1]
    qdb = rand_key()
    CHAR_DB[qdb] = query
    auth = False
    if await AUTH_USERS.find_one({"id": auser}):
        auth = True
    result = await get_character(qdb, 1, auth=auth, user=auser)
    if len(result) == 1:
        k = await message.reply_text(result[0])
        await asyncio.sleep(5)
        return await k.delete()
    img = result[0]
    cap_text = result[1][0]
    buttons = get_btns(
        "CHARACTER", user=user, lsqry=qdb, lspage=1, result=result, auth=auth
    )
    try:
        await client.send_photo(gid, img, caption=cap_text, reply_markup=buttons)
    except (WebpageMediaEmpty, WebpageCurlFailed):
        await clog("Mikobot", img, "LINK", msg=message)
        await client.send_photo(gid, failed_pic, caption=cap_text, reply_markup=buttons)


@app.on_message(
    filters.command(["anilist", f"anilist{BOT_USERNAME}"], prefixes=PREFIX_HANDLER)
)
@control_user
async def anilist_cmd(client: Client, message: Message, mdata: dict):
    text = mdata["text"].split(" ", 1)
    gid = mdata["chat"]["id"]
    try:
        user = mdata["from_user"]["id"]
        auser = mdata["from_user"]["id"]
    except KeyError:
        user = mdata["sender_chat"]["id"]
        ufc = await gcc(user)
        if ufc is not None:
            auser = ufc
        else:
            auser = user
    find_gc = await DC.find_one({"_id": gid})
    if find_gc is not None and "anilist" in find_gc["cmd_list"].split():
        return
    if len(text) == 1:
        k = await message.reply_text(
            "Please give a query to search about\nexample: /anilist Sword Art Online"
        )
        await asyncio.sleep(5)
        return await k.delete()
    query = text[1]
    qdb = rand_key()
    ANIME_DB[qdb] = query
    auth = False
    if await AUTH_USERS.find_one({"id": auser}):
        auth = True
    result = await get_anilist(
        qdb, 1, auth=auth, user=auser, cid=gid if gid != user else None
    )
    if len(result) == 1:
        k = await message.reply_text(result[0])
        await asyncio.sleep(5)
        return await k.delete()
    pic, msg = result[0], result[1][0]
    buttons = get_btns(
        "ANIME", lsqry=qdb, lspage=1, result=result, user=user, auth=auth
    )
    if await SFW_GRPS.find_one({"id": gid}) and result[2].pop() == "True":
        buttons = get_btns(
            "ANIME",
            lsqry=qdb,
            lspage=1,
            result=result,
            user=user,
            auth=auth,
            sfw="True",
        )
        await client.send_photo(
            gid,
            no_pic[random.randint(0, 4)],
            caption="This anime is marked 18+ and not allowed in this group",
            reply_markup=buttons,
        )
        return
    try:
        await client.send_photo(gid, pic, caption=msg, reply_markup=buttons)
    except (WebpageMediaEmpty, WebpageCurlFailed):
        await clog("Mikobot", pic, "LINK", msg=message)
        await client.send_photo(gid, failed_pic, caption=msg, reply_markup=buttons)


@app.on_message(filters.command(["top", f"top{BOT_USERNAME}"], prefixes=PREFIX_HANDLER))
@control_user
async def top_tags_cmd(client: Client, message: Message, mdata: dict):
    query = mdata["text"].split(" ", 1)
    gid = mdata["chat"]["id"]
    find_gc = await DC.find_one({"_id": gid})
    if find_gc is not None and "top" in find_gc["cmd_list"].split():
        return
    get_tag = "None"
    if len(query) == 2:
        get_tag = query[1]
    try:
        user = mdata["from_user"]["id"]
    except KeyError:
        user = mdata["sender_chat"]["id"]
    result = await get_top_animes(get_tag, 1, user)
    if len(result) == 1:
        k = await message.reply_text(result[0])
        await asyncio.sleep(5)
        return await k.delete()
    if await SFW_GRPS.find_one({"id": gid}) and str(result[0][1]) == "True":
        return await message.reply_text("No nsfw stuff allowed in this group!!!")
    msg, buttons = result
    await client.send_message(
        gid, msg[0], reply_markup=buttons if buttons != "" else None
    )


@app.on_message(
    filters.command(["studio", f"studio{BOT_USERNAME}"], prefixes=PREFIX_HANDLER)
)
@control_user
async def studio_cmd(client: Client, message: Message, mdata: dict):
    text = mdata["text"].split(" ", 1)
    gid = mdata["chat"]["id"]
    find_gc = await DC.find_one({"_id": gid})
    if find_gc is not None and "studio" in find_gc["cmd_list"].split():
        return
    if len(text) == 1:
        x = await message.reply_text(
            "Please give a query to search about!!!\nExample: /studio ufotable"
        )
        await asyncio.sleep(5)
        await x.delete()
        return
    query = text[1]
    qdb = rand_key()
    STUDIO_DB[qdb] = query
    auth = False
    try:
        user = mdata["from_user"]["id"]
        auser = mdata["from_user"]["id"]
    except KeyError:
        user = mdata["sender_chat"]["id"]
        ufc = await gcc(user)
        if ufc is not None:
            auser = ufc
        else:
            auser = user
    if await AUTH_USERS.find_one({"id": auser}):
        auth = True
    result = await get_studios(qdb, 1, user=auser, duser=user, auth=auth)
    if len(result) == 1:
        x = await message.reply_text("No results found!!!")
        await asyncio.sleep(5)
        return await x.delete()
    msg, buttons = result[0], result[1]
    await client.send_message(gid, msg, reply_markup=buttons if buttons != "" else None)


@app.on_message(
    filters.command(["airing", f"airing{BOT_USERNAME}"], prefixes=PREFIX_HANDLER)
)
@control_user
async def airing_cmd(client: Client, message: Message, mdata: dict):
    """Get Airing Detail of Anime"""
    text = mdata["text"].split(" ", 1)
    gid = mdata["chat"]["id"]
    find_gc = await DC.find_one({"_id": gid})
    if find_gc is not None and "airing" in find_gc["cmd_list"].split():
        return
    if len(text) == 1:
        k = await message.reply_text(
            """Please give a query to search about

example: /airing Sword Art Online"""
        )
        await asyncio.sleep(5)
        return await k.delete()
    query = text[1]
    qdb = rand_key()
    AIRING_DB[qdb] = query
    auth = False
    try:
        user = mdata["from_user"]["id"]
        auser = mdata["from_user"]["id"]
    except KeyError:
        user = mdata["sender_chat"]["id"]
        ufc = await gcc(user)
        if ufc is not None:
            auser = ufc
        else:
            auser = user
    if await AUTH_USERS.find_one({"id": auser}):
        auth = True
    result = await get_airing(qdb, 1, auth=auth, user=auser)
    if len(result) == 1:
        k = await message.reply_text(result[0])
        await asyncio.sleep(5)
        return await k.delete()
    coverImg, out = result[0]
    btn = get_btns("AIRING", user=user, result=result, auth=auth, lsqry=qdb, lspage=1)
    if await SFW_GRPS.find_one({"id": gid}) and result[2].pop() == "True":
        btn = get_btns(
            "AIRING",
            user=user,
            result=result,
            auth=auth,
            lsqry=qdb,
            lspage=1,
            sfw="True",
        )
        await client.send_photo(
            gid,
            no_pic[random.randint(0, 4)],
            caption="This anime is marked 18+ and not allowed in this group",
            reply_markup=btn,
        )
        return
    try:
        await client.send_photo(gid, coverImg, caption=out, reply_markup=btn)
    except (WebpageMediaEmpty, WebpageCurlFailed):
        await clog("Mikobot", coverImg, "LINK", msg=message)
        await client.send_photo(gid, failed_pic, caption=out, reply_markup=btn)


setting_text = """
<b>This allows you to change group settings</b>
        
NSFW toggle switches on filtering of 18+ marked content

Airing notifications notifies about airing of anime in recent

Crunchyroll updates will toggle notifications about release of animes on crunchyroll site

Subsplease updates will toggle notifications about release of animes on subsplease site

Click Headlines button to enable headlines. You can choose from given sources"""


@app.on_message(
    ~filters.private
    & filters.command(
        ["anisettings", f"anisettings{BOT_USERNAME}"], prefixes=PREFIX_HANDLER
    )
)
@control_user
async def settings_cmd(client: Client, message: Message, mdata: dict):
    cid = mdata["chat"]["id"]
    try:
        user = mdata["from_user"]["id"]
    except KeyError:
        user = mdata["sender_chat"]["id"]
    type_ = mdata["chat"]["type"]
    try:
        status = (await app.get_chat_member(cid, user)).status
    except UserNotParticipant:
        status = None
    if (
        user in BOT_OWNER
        or status in [ADMINISTRATOR, CHAT_OWNER]
        or type_ == ChatType.CHANNEL
        or user == cid
    ):
        sfw = "NSFW: Allowed"
        if await SFW_GRPS.find_one({"id": cid}):
            sfw = "NSFW: Not Allowed"
        notif = "Airing notifications: OFF"
        if await AG.find_one({"_id": cid}):
            notif = "Airing notifications: ON"
        cr = "Crunchyroll Updates: OFF"
        if await CG.find_one({"_id": cid}):
            cr = "Crunchyroll Updates: ON"
        sp = "Subsplease Updates: OFF"
        if await SG.find_one({"_id": cid}):
            sp = "Subsplease Updates: ON"
        await message.reply_text(
            text=setting_text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text=sfw, callback_data=f"settogl_sfw_{cid}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=notif, callback_data=f"settogl_notif_{cid}"
                        )
                    ],
                    [InlineKeyboardButton(text=cr, callback_data=f"settogl_cr_{cid}")],
                    [InlineKeyboardButton(text=sp, callback_data=f"settogl_sp_{cid}")],
                    [
                        InlineKeyboardButton(
                            text="Headlines", callback_data=f"headlines_call_{cid}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="Change UI", callback_data=f"cui_call_{cid}"
                        )
                    ],
                ]
            ),
        )


@app.on_message(
    filters.command(["browse", f"browse{BOT_USERNAME}"], prefixes=PREFIX_HANDLER)
)
@control_user
async def browse_cmd(client: Client, message: Message, mdata: dict):
    try:
        user = mdata["from_user"]["id"]
    except KeyError:
        user = mdata["sender_chat"]["id"]
    gid = mdata["chat"]["id"]
    find_gc = await DC.find_one({"_id": gid})
    if find_gc is not None and "browse" in find_gc["cmd_list"].split():
        return
    up = "Upcoming"
    tr = "• Trending •"
    pp = "Popular"
    btns = [
        [
            InlineKeyboardButton(tr, callback_data=f"browse_{tr.lower()}_{user}"),
            InlineKeyboardButton(pp, callback_data=f"browse_{pp.lower()}_{user}"),
            InlineKeyboardButton(up, callback_data=f"browse_{up.lower()}_{user}"),
        ]
    ]
    msg = await browse_("trending")
    await client.send_message(gid, msg, reply_markup=InlineKeyboardMarkup(btns))


@app.on_message(
    filters.command(
        ["gettags", f"gettags{BOT_USERNAME}", "getgenres", f"getgenres{BOT_USERNAME}"],
        prefixes=PREFIX_HANDLER,
    )
)
@control_user
async def list_tags_genres_cmd(client, message: Message, mdata: dict):
    gid = mdata["chat"]["id"]
    text = mdata["text"]
    find_gc = await DC.find_one({"_id": gid})
    if find_gc is not None and "gettags" in (
        text.split()[0] and find_gc["cmd_list"].split()
    ):
        return
    if find_gc is not None and "getgenres" in (
        text.split()[0] and find_gc["cmd_list"].split()
    ):
        return
    if await SFW_GRPS.find_one({"id": gid}) and "nsfw" in text:
        return await message.reply_text("No nsfw allowed here!!!")
    msg = (
        (await get_all_tags(text))
        if "gettags" in text.split()[0]
        else (await get_all_genres())
    )
    await message.reply_text(msg)


@app.on_callback_query(filters.regex(pattern=r"page_(.*)"))
@check_user
async def page_btn(client: Client, cq: CallbackQuery, cdata: dict):
    kek, media, query, page, auth, user = cq.data.split("_")
    gid = cdata["message"]["chat"]["id"]
    if media == "ANIME":
        try:
            ANIME_DB[query]
        except KeyError:
            return await cq.answer("Query Expired!!!\nCreate new one", show_alert=True)
    if media == "MANGA":
        try:
            MANGA_DB[query]
        except KeyError:
            return await cq.answer("Query Expired!!!\nCreate new one", show_alert=True)
    if media == "CHARACTER":
        try:
            CHAR_DB[query]
        except KeyError:
            return await cq.answer("Query Expired!!!\nCreate new one", show_alert=True)
    if media == "AIRING":
        try:
            AIRING_DB[query]
        except KeyError:
            return await cq.answer("Query Expired!!!\nCreate new one", show_alert=True)
    authbool = bool(1) if auth == "True" else bool(0)
    if "-100" in str(user):
        auser = await gcc(user)
    else:
        auser = user
    if media in ["ANIME", "MANGA"]:
        result = await (get_anilist if media == "ANIME" else get_manga)(
            query,
            int(page),
            auth=authbool,
            user=int(auser),
            cid=gid if gid != user else None,
        )
    else:
        result = await (get_character if media == "CHARACTER" else get_airing)(
            query, int(page), auth=authbool, user=int(auser)
        )
    if "No results Found" in result:
        await cq.answer("No more results available!!!", show_alert=True)
        return
    pic, msg = result[0], result[1][0]
    if media == "AIRING":
        pic, msg = result[0][0], result[0][1]
    button = get_btns(
        media, lsqry=query, lspage=int(page), result=result, user=user, auth=authbool
    )
    if (
        await SFW_GRPS.find_one({"id": gid})
        and media != "CHARACTER"
        and result[2].pop() == "True"
    ):
        button = get_btns(
            media,
            lsqry=query,
            lspage=int(page),
            result=result,
            user=user,
            auth=authbool,
            sfw="True",
        )
        await cq.edit_message_media(
            InputMediaPhoto(
                no_pic[random.randint(0, 4)],
                caption="""
This material is marked 18+ and not allowed in this group""",
            ),
            reply_markup=button,
        )
        return
    try:
        await cq.edit_message_media(
            InputMediaPhoto(pic, caption=msg), reply_markup=button
        )
    except (WebpageMediaEmpty, WebpageCurlFailed):
        await clog("Mikobot", pic, "LINK", msg=cq)
        await cq.edit_message_media(
            InputMediaPhoto(failed_pic, caption=msg), reply_markup=button
        )
    await cq.answer()


@app.on_callback_query(filters.regex(pattern=r"pgstudio_(.*)"))
@check_user
async def studio_pg_btn(client: Client, cq: CallbackQuery, cdata: dict):
    kek, page, qry, auth, user = cdata["data"].split("_")
    authbool = bool(1) if auth == "True" else bool(0)
    try:
        STUDIO_DB[qry]
    except KeyError:
        return await cq.answer("Query Expired!!!\nCreate new one", show_alert=True)
    if "-100" in str(user):
        auser = await gcc(user)
    else:
        auser = user
    result = await get_studios(qry, page=page, user=auser, duser=user, auth=authbool)
    if len(result) == 1:
        return await cq.answer("No more results available!!!", show_alert=True)
    msg, buttons = result[0], result[1]
    await cq.edit_message_text(msg, reply_markup=buttons)


@app.on_callback_query(filters.regex(pattern=r"stuani_(.*)"))
@check_user
async def studio_ani_btn(client: Client, cq: CallbackQuery, cdata: dict):
    kek, page, id_, rp, qry, auth, user = cdata["data"].split("_")
    authbool = bool(1) if auth == "True" else bool(0)
    if "-100" in str(user):
        auser = await gcc(user)
    else:
        auser = user
    result = await get_studio_animes(id_, page, qry, rp, auser, user, authbool)
    if len(result) == 1:
        return await cq.answer("No results available!!!", show_alert=True)
    msg, buttons = result[0], result[1]
    await cq.edit_message_text(msg, reply_markup=buttons)


@app.on_callback_query(filters.regex(pattern=r"btn_(.*)"))
@check_user
async def anime_btn(client: Client, cq: CallbackQuery, cdata: dict):
    await cq.answer()
    query = cdata["data"].split("_")
    idm = query[1]
    user = int(query.pop())
    if "-100" in str(user):
        auser = await gcc(user)
    else:
        auser = user
    authbool = bool(1) if query[2] == "True" else bool(0)
    vars_ = {"id": int(idm)}
    cid = cdata["message"]["chat"]["id"]
    result = await get_anime(
        vars_, auth=authbool, user=auser, cid=cid if cid != user else None
    )
    pic, msg = result[0], result[1]
    btns = get_btns("ANIME", result=result, user=user, auth=authbool)
    try:
        await cq.edit_message_media(
            InputMediaPhoto(pic, caption=msg), reply_markup=btns
        )
    except (WebpageMediaEmpty, WebpageCurlFailed):
        await clog("Mikobot", pic, "LINK", msg=cq)
        await cq.edit_message_media(
            InputMediaPhoto(failed_pic, caption=msg), reply_markup=btns
        )


@app.on_callback_query(filters.regex(pattern=r"topanimu_(.*)"))
@check_user
async def top_tags_btn(client: Client, cq: CallbackQuery, cdata: dict):
    await cq.answer()
    kek, gnr, page, user = cdata["data"].split("_")
    result = await get_top_animes(gnr, page=page, user=user)
    msg, buttons = result[0][0], result[1]
    await cq.edit_message_text(msg, reply_markup=buttons)


@app.on_callback_query(filters.regex(pattern=r"settogl_(.*)"))
async def nsfw_toggle_btn(client: Client, cq: CallbackQuery):
    cus = cq.from_user.id
    gid = cq.data.split("_").pop()
    try:
        k = (await client.get_chat_member(gid, cus)).status
    except UserNotParticipant:
        await cq.answer()
        return
    if cus not in BOT_OWNER and k == MEMBER:
        await cq.answer(
            "You don't have enough permissions to change this!!!", show_alert=True
        )
        return
    query = cq.data.split("_")
    if await SFW_GRPS.find_one({"id": int(query[2])}):
        sfw = "NSFW: Not Allowed"
    else:
        sfw = "NSFW: Allowed"
    if await AG.find_one({"_id": int(query[2])}):
        notif = "Airing notifications: ON"
    else:
        notif = "Airing notifications: OFF"
    if await CG.find_one({"_id": int(query[2])}):
        cr = "Crunchyroll Updates: ON"
    else:
        cr = "Crunchyroll Updates: OFF"
    if await SG.find_one({"_id": int(query[2])}):
        sp = "Subsplease Updates: ON"
    else:
        sp = "Subsplease Updates: OFF"
    if query[1] == "sfw":
        if await SFW_GRPS.find_one({"id": int(query[2])}):
            await SFW_GRPS.find_one_and_delete({"id": int(query[2])})
            sfw = "NSFW: Allowed"
        else:
            await SFW_GRPS.insert_one({"id": int(query[2])})
            sfw = "NSFW: Not Allowed"
    if query[1] == "notif":
        if await AG.find_one({"_id": int(query[2])}):
            await AG.find_one_and_delete({"_id": int(query[2])})
            notif = "Airing notifications: OFF"
        else:
            await AG.insert_one({"_id": int(query[2])})
            notif = "Airing notifications: ON"
    if query[1] == "cr":
        if await CG.find_one({"_id": int(query[2])}):
            await CG.find_one_and_delete({"_id": int(query[2])})
            cr = "Crunchyroll Updates: OFF"
        else:
            await CG.insert_one({"_id": int(query[2])})
            cr = "Crunchyroll Updates: ON"
    if query[1] == "sp":
        if await SG.find_one({"_id": int(query[2])}):
            await SG.find_one_and_delete({"_id": int(query[2])})
            sp = "Subsplease Updates: OFF"
        else:
            await SG.insert_one({"_id": int(query[2])})
            sp = "Subsplease Updates: ON"
    btns = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(text=sfw, callback_data=f"settogl_sfw_{query[2]}")],
            [
                InlineKeyboardButton(
                    text=notif, callback_data=f"settogl_notif_{query[2]}"
                )
            ],
            [InlineKeyboardButton(text=cr, callback_data=f"settogl_cr_{query[2]}")],
            [InlineKeyboardButton(text=sp, callback_data=f"settogl_sp_{query[2]}")],
            [
                InlineKeyboardButton(
                    text="Headlines", callback_data=f"headlines_call_{query[2]}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Change UI", callback_data=f"cui_call_{query[2]}"
                )
            ],
        ]
    )
    await cq.answer()
    if query[1] == "call":
        await cq.edit_message_text(text=setting_text, reply_markup=btns)
    await cq.edit_message_reply_markup(reply_markup=btns)


@app.on_callback_query(filters.regex(pattern=r"myacc_(.*)"))
@check_user
async def flex_btn(client: Client, cq: CallbackQuery, cdata: dict):
    await cq.answer()
    query = cdata["data"].split("_")[1]
    user = cdata["data"].split("_").pop()
    if "-100" in str(user):
        auser = await gcc(user)
    else:
        auser = user
    result = await get_user_activity(int(query), user=int(auser), duser=int(user))
    pic, msg, btns = result
    try:
        await cq.edit_message_media(
            InputMediaPhoto(pic, caption=msg), reply_markup=btns
        )
    except (WebpageMediaEmpty, WebpageCurlFailed):
        await clog("Mikobot", pic, "LINK", msg=cq)
        await cq.edit_message_media(
            InputMediaPhoto(failed_pic, caption=msg), reply_markup=btns
        )


@app.on_callback_query(filters.regex(pattern=r"myfavs_(.*)"))
@check_user
async def list_favourites_btn(client: Client, cq: CallbackQuery, cdata: dict):
    await cq.answer()
    q = cdata["data"].split("_")
    btn = [
        [
            InlineKeyboardButton(
                "ANIME", callback_data=f"myfavqry_ANIME_{q[1]}_1_{q[2]}_{q[3]}"
            ),
            InlineKeyboardButton(
                "CHARACTER", callback_data=f"myfavqry_CHAR_{q[1]}_1_{q[2]}_{q[3]}"
            ),
            InlineKeyboardButton(
                "MANGA", callback_data=f"myfavqry_MANGA_{q[1]}_1_{q[2]}_{q[3]}"
            ),
        ]
    ]
    if q[2] == "yes":
        btn.append([InlineKeyboardButton("BACK", callback_data=f"getusrbc_{q[3]}")])
    else:
        btn.append(
            [InlineKeyboardButton("PROFILE", url=f"https://anilist.co/user/{q[1]}")]
        )
    try:
        await cq.edit_message_media(
            InputMediaPhoto(
                f"https://img.anili.st/user/{q[1]}?a={time.time()}",
                caption="Choose one of the below options",
            ),
            reply_markup=InlineKeyboardMarkup(btn),
        )
    except (WebpageMediaEmpty, WebpageCurlFailed):
        await clog(
            "Mikobot",
            f"https://img.anili.st/user/{q[1]}?a={time.time()}",
            "LINK",
            msg=cq,
        )
        await cq.edit_message_media(
            InputMediaPhoto(failed_pic, caption="Choose one of the below options"),
            reply_markup=InlineKeyboardMarkup(btn),
        )


@app.on_callback_query(filters.regex(pattern=r"myfavqry_(.*)"))
@check_user
async def favourites_btn(client: Client, cq: CallbackQuery, cdata: dict):
    await cq.answer()
    q = cdata["data"].split("_")
    if "-100" in str(q[5]):
        auser = await gcc(q[5])
    else:
        auser = q[5]
    pic, msg, btns = await get_user_favourites(
        q[2], int(auser), q[1], q[3], q[4], duser=int(q[5])
    )
    try:
        await cq.edit_message_media(
            InputMediaPhoto(pic, caption=msg), reply_markup=btns
        )
    except (WebpageMediaEmpty, WebpageCurlFailed):
        await clog("Mikobot", pic, "LINK", msg=cq)
        await cq.edit_message_media(
            InputMediaPhoto(failed_pic, caption=msg), reply_markup=btns
        )


@app.on_callback_query(filters.regex(pattern=r"getusrbc_(.*)"))
@check_user
async def get_user_back_btn(client: Client, cq: CallbackQuery, cdata: dict):
    await cq.answer()
    query = cdata["data"].split("_")[1]
    if "-100" in str(query):
        auser = await gcc(query)
    else:
        auser = query
    result = await get_user(None, "flex", user=int(auser), display_user=query)
    pic, msg, btns = result
    try:
        await cq.edit_message_media(
            InputMediaPhoto(pic, caption=msg), reply_markup=btns
        )
    except (WebpageMediaEmpty, WebpageCurlFailed):
        await clog("Mikobot", pic, "LINK", msg=cq)
        await cq.edit_message_media(
            InputMediaPhoto(failed_pic, caption=msg), creply_markup=btns
        )


@app.on_callback_query(filters.regex(pattern=r"fav_(.*)"))
@check_user
async def toggle_favourites_btn(client: Client, cq: CallbackQuery, cdata: dict):
    query = cdata["data"].split("_")
    if query[1] == "ANIME" and len(query) > 4:
        try:
            ANIME_DB[query[3]]
        except KeyError:
            return await cq.answer("Query Expired!!!\nCreate new one", show_alert=True)
    if query[1] == "MANGA":
        try:
            MANGA_DB[query[3]]
        except KeyError:
            return await cq.answer("Query Expired!!!\nCreate new one", show_alert=True)
    if query[1] == "CHARACTER":
        try:
            CHAR_DB[query[3]]
        except KeyError:
            return await cq.answer("Query Expired!!!\nCreate new one", show_alert=True)
    if query[1] == "STUDIO":
        try:
            STUDIO_DB[query[3]]
        except KeyError:
            return await cq.answer("Query Expired!!!\nCreate new one", show_alert=True)
    idm = int(query[2])
    user = int(query.pop())
    if "-100" in str(user):
        auser = await gcc(user)
    else:
        auser = user
    gid = cdata["message"]["chat"]["id"]
    rslt = await toggle_favourites(id_=idm, media=query[1], user=auser)
    if rslt == "ok":
        await cq.answer("Updated", show_alert=True)
    else:
        return await cq.answer("Failed to update!!!", show_alert=True)
    result = (
        (
            await get_anime(
                {"id": idm}, auth=True, user=auser, cid=gid if gid != user else None
            )
        )
        if query[1] == "ANIME" and len(query) == 3
        else (
            (
                await get_anilist(
                    query[3],
                    page=int(query[4]),
                    auth=True,
                    user=auser,
                    cid=gid if gid != user else None,
                )
            )
            if query[1] == "ANIME" and len(query) != 3
            else (
                (
                    await get_manga(
                        query[3],
                        page=int(query[4]),
                        auth=True,
                        user=auser,
                        cid=gid if gid != user else None,
                    )
                )
                if query[1] == "MANGA"
                else (
                    (
                        await get_airing(
                            query[3], auth=True, user=auser, ind=int(query[4])
                        )
                    )
                    if query[1] == "AIRING"
                    else (
                        (
                            await get_character(
                                query[3], int(query[4]), auth=True, user=auser
                            )
                        )
                        if query[1] == "CHARACTER"
                        else (
                            await get_studios(
                                query[3],
                                int(query[4]),
                                user=auser,
                                auth=True,
                                duser=user,
                            )
                        )
                    )
                )
            )
        )
    )
    if query[1] == "STUDIO":
        return await cq.edit_message_text(result[0], reply_markup=result[1])
    pic, msg = (
        (result[0], result[1])
        if query[1] == "ANIME" and len(query) == 3
        else (result[0]) if query[1] == "AIRING" else (result[0], result[1][0])
    )
    btns = get_btns(
        query[1],
        result=result,
        user=user,
        auth=True,
        lsqry=query[3] if len(query) != 3 else None,
        lspage=int(query[4]) if len(query) != 3 else None,
    )
    try:
        await cq.edit_message_media(
            InputMediaPhoto(pic, caption=msg), reply_markup=btns
        )
    except (WebpageMediaEmpty, WebpageCurlFailed):
        await clog("Mikobot", pic, "LINK", msg=cq)
        await cq.edit_message_media(
            InputMediaPhoto(failed_pic, caption=msg), reply_markup=btns
        )


@app.on_callback_query(filters.regex(pattern=r"(lsadd|lsupdt)_(.*)"))
@check_user
async def list_update_anilist_btn(client: Client, cq: CallbackQuery, cdata: dict):
    stts_ls = ["COMPLETED", "CURRENT", "PLANNING", "DROPPED", "PAUSED", "REPEATING"]
    query = cdata["data"].split("_")
    btns = []
    row = []
    for i in stts_ls:
        row.append(
            InlineKeyboardButton(
                text=i,
                callback_data=(
                    cq.data.replace("lsadd", f"lsas_{i}")
                    if query[0] == "lsadd"
                    else cq.data.replace("lsupdt", f"lsus_{i}")
                ),
            )
        )
        if len(row) == 3:
            btns.append(row)
            row = []
    if query[0] == "lsupdt":
        btns.append(
            [
                InlineKeyboardButton(
                    "DELETE", callback_data=cq.data.replace("lsupdt", f"dlt_{i}")
                )
            ]
        )
    await cq.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btns))


@app.on_callback_query(
    filters.regex(pattern=r"browse_(upcoming|trending|popular)_(.*)")
)
@check_user
async def browse_btn(client: Client, cq: CallbackQuery, cdata: dict):
    query = cdata["data"].split("_")
    if "•" in query[1]:
        return
    msg = await browse_(query[1])
    up = "Upcoming" if query[1] != "upcoming" else "• Upcoming •"
    tr = "Trending" if query[1] != "trending" else "• Trending •"
    pp = "Popular" if query[1] != "popular" else "• Popular •"
    btns = [
        [
            InlineKeyboardButton(tr, callback_data=f"browse_{tr.lower()}_{query[2]}"),
            InlineKeyboardButton(pp, callback_data=f"browse_{pp.lower()}_{query[2]}"),
            InlineKeyboardButton(up, callback_data=f"browse_{up.lower()}_{query[2]}"),
        ]
    ]
    await cq.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(btns))


@app.on_callback_query(filters.regex(pattern=r"(lsas|lsus|dlt)_(.*)"))
@check_user
async def update_anilist_btn(client: Client, cq: CallbackQuery, cdata: dict):
    query = cdata["data"].split("_")
    if query[2] == "ANIME":
        if len(query) == 7:
            try:
                ANIME_DB[query[4]]
            except KeyError:
                return await cq.answer(
                    "Query Expired!!!\nCreate new one", show_alert=True
                )
        if len(query) == 8:
            try:
                ANIME_DB[query[5]]
            except KeyError:
                return await cq.answer(
                    "Query Expired!!!\nCreate new one", show_alert=True
                )
    if query[2] == "MANGA":
        if len(query) == 7:
            try:
                MANGA_DB[query[4]]
            except KeyError:
                return await cq.answer(
                    "Query Expired!!!\nCreate new one", show_alert=True
                )
        if len(query) == 8:
            try:
                MANGA_DB[query[5]]
            except KeyError:
                return await cq.answer(
                    "Query Expired!!!\nCreate new one", show_alert=True
                )
    idm = int(query[3])
    user = int(query.pop())
    if "-100" in str(user):
        auser = await gcc(user)
    else:
        auser = user
    gid = cdata["message"]["chat"]["id"]
    eid = None
    if query[0] != "lsas":
        eid = int(query[4])
    rslt = await update_anilist(
        id_=idm, req=query[0], status=query[1], user=auser, eid=eid
    )
    if rslt == "ok":
        await cq.answer("Updated", show_alert=True)
    else:
        await cq.answer(
            "Something unexpected happened and operation failed successfully",
            show_alert=True,
        )
        return
    result = (
        (
            await get_anime(
                {"id": idm}, auth=True, user=auser, cid=gid if gid != user else None
            )
        )
        if query[2] == "ANIME" and (len(query) == 4 or len(query) == 5)
        else (
            (
                await get_anilist(
                    query[4],
                    page=int(query[5]),
                    auth=True,
                    user=auser,
                    cid=gid if gid != user else None,
                )
            )
            if query[2] == "ANIME" and len(query) == 6
            else (
                (
                    await get_anilist(
                        query[5],
                        page=int(query[6]),
                        auth=True,
                        user=auser,
                        cid=gid if gid != user else None,
                    )
                )
                if query[2] == "ANIME" and len(query) == 7
                else (
                    (
                        await get_manga(
                            query[4],
                            page=int(query[5]),
                            auth=True,
                            user=auser,
                            cid=gid if gid != user else None,
                        )
                    )
                    if query[2] == "MANGA" and len(query) == 6
                    else (
                        (
                            await get_manga(
                                query[5],
                                page=int(query[6]),
                                auth=True,
                                user=auser,
                                cid=gid if gid != user else None,
                            )
                        )
                        if query[2] == "MANGA" and len(query) == 7
                        else (
                            await get_airing(
                                query[4] if eid is None else query[5],
                                auth=True,
                                user=auser,
                                ind=int(query[5] if eid is None else query[6]),
                            )
                        )
                    )
                )
            )
        )
    )
    pic, msg = (
        (result[0], result[1])
        if query[2] == "ANIME" and (len(query) == 4 or len(query) == 5)
        else (result[0]) if query[2] == "AIRING" else (result[0], result[1][0])
    )
    btns = get_btns(
        query[2],
        result=result,
        user=user,
        auth=True,
        lsqry=query[4] if len(query) == 6 else query[5] if len(query) == 7 else None,
        lspage=(
            int(query[5])
            if len(query) == 6
            else int(query[6]) if len(query) == 7 else None
        ),
    )
    try:
        await cq.edit_message_media(
            InputMediaPhoto(pic, caption=msg), reply_markup=btns
        )
    except (WebpageMediaEmpty, WebpageCurlFailed):
        await clog("Mikobot", pic, "LINK", msg=cq)
        await cq.edit_message_media(
            InputMediaPhoto(failed_pic, caption=msg), reply_markup=btns
        )


@app.on_callback_query(filters.regex(pattern=r"(desc|ls|char)_(.*)"))
@check_user
async def additional_info_btn(client: Client, cq: CallbackQuery, cdata: dict):
    q = cdata["data"].split("_")
    kek, qry, ctgry = q[0], q[1], q[2]
    info = (
        "<b>Description</b>"
        if kek == "desc"
        else "<b>Series List</b>" if kek == "ls" else "<b>Characters List</b>"
    )
    page = 0
    lsqry = f"_{q[3]}" if len(q) > 6 else ""
    lspg = f"_{q[4]}" if len(q) > 6 else ""
    if kek == "char":
        page = q[6] if len(q) > 6 else q[4]
    rjsdata = await get_additional_info(qry, ctgry, kek, page=int(page))
    pic, result = rjsdata[0], rjsdata[1]
    button = []
    spoiler = False
    bot = BOT_USERNAME
    if result is None:
        await cq.answer("No description available!!!", show_alert=True)
        return
    if "~!" in result and "!~" in result:
        result = re.sub(r"~!.*!~", "[Spoiler]", result)
        spoiler = True
        button.append(
            [
                InlineKeyboardButton(
                    text="VIEW SPOILER",
                    url=f"https://t.me/{bot}/?astart=des_{ctgry}_{qry}_desc",
                )
            ]
        )
    if len(result) > 1000:
        result = result[:940] + "..."
        if spoiler is False:
            result += "\n\nFor more info click below given button"
            button.append(
                [
                    InlineKeyboardButton(
                        text="MORE INFO",
                        url=f"https://t.me/{bot}/?astart=des_{ctgry}_{qry}_{kek}",
                    )
                ]
            )
    add_ = ""
    user = q.pop()
    if kek == "char":
        btndata = rjsdata[2]
        if btndata["lastPage"] != 1:
            qs = q[5] if len(q) != 5 else q[3]
            pre = f"{kek}_{qry}_{ctgry}{lsqry}{lspg}_{qs}_{int(page)-1}_{user}"
            nex = f"{kek}_{qry}_{ctgry}{lsqry}{lspg}_{qs}_{int(page)+1}_{user}"
            if page == "1":
                button.append([InlineKeyboardButton(text="NEXT", callback_data=nex)])
            elif btndata["lastPage"] == int(page):
                button.append([InlineKeyboardButton(text="PREV", callback_data=pre)])
            else:
                button.append(
                    [
                        InlineKeyboardButton(text="PREV", callback_data=pre),
                        InlineKeyboardButton(text="NEXT", callback_data=nex),
                    ]
                )
        add_ = f"\n\nTotal Characters: {btndata['total']}"
    msg = f"{info}:\n\n{result+add_}"
    cbd = (
        f"btn_{qry}_{q[3]}_{user}"
        if len(q) <= 5
        else (
            f"page_ANIME{lsqry}{lspg}_{q[5]}_{user}"
            if ctgry == "ANI"
            else f"page_CHARACTER{lsqry}{lspg}_{q[5]}_{user}"
        )
    )
    button.append([InlineKeyboardButton(text="BACK", callback_data=cbd)])
    try:
        await cq.edit_message_media(
            InputMediaPhoto(pic, caption=msg), reply_markup=InlineKeyboardMarkup(button)
        )
    except (WebpageMediaEmpty, WebpageCurlFailed):
        await clog("Mikobot", pic, "LINK", msg=cq)
        await cq.edit_message_media(
            InputMediaPhoto(failed_pic, caption=msg),
            reply_markup=InlineKeyboardMarkup(button),
        )
    await cq.answer()


@app.on_callback_query(filters.regex(pattern=r"lsc_(.*)"))
@check_user
async def featured_in_btn(client: Client, cq: CallbackQuery, cdata: dict):
    kek, idm, qry, pg, auth, usr = cdata["data"].split("_")
    result = await get_featured_in_lists(int(idm), "ANI")
    req = "lscm"
    if result[0] is False:
        result = await get_featured_in_lists(int(idm), "MAN")
        req = None
        if result[0] is False:
            await cq.answer("No Data Available!!!", show_alert=True)
            return
    [msg, total], pic = result
    button = []
    totalpg, kek = divmod(total, 15)
    if kek != 0:
        totalpg + 1
    if total > 15:
        button.append(
            [
                InlineKeyboardButton(
                    text="NEXT", callback_data=f"lsca_{idm}_1_{qry}_{pg}_{auth}_{usr}"
                )
            ]
        )
    if req is not None:
        button.append(
            [
                InlineKeyboardButton(
                    text="MANGA", callback_data=f"lscm_{idm}_0_{qry}_{pg}_{auth}_{usr}"
                )
            ]
        )
    button.append(
        [
            InlineKeyboardButton(
                text="BACK", callback_data=f"page_CHARACTER_{qry}_{pg}_{auth}_{usr}"
            )
        ]
    )
    try:
        await cq.edit_message_media(
            InputMediaPhoto(pic, caption=msg), reply_markup=InlineKeyboardMarkup(button)
        )
    except (WebpageMediaEmpty, WebpageCurlFailed):
        await clog("Mikobot", pic, "LINK", msg=cq)
        await cq.edit_message_media(
            InputMediaPhoto(failed_pic, caption=msg),
            reply_markup=InlineKeyboardMarkup(button),
        )


@app.on_callback_query(filters.regex(pattern=r"lsc(a|m)_(.*)"))
@check_user
async def featured_in_switch_btn(client: Client, cq: CallbackQuery, cdata: dict):
    req, idm, reqpg, qry, pg, auth, user = cdata["data"].split("_")
    result = await get_featured_in_lists(
        int(idm), "MAN" if req == "lscm" else "ANI", page=int(reqpg)
    )
    reqb = "lsca" if req == "lscm" else "lscm"
    bt = "Anime" if req == "lscm" else "Manga"
    if result[0] is False:
        await cq.answer("No Data Available!!!", show_alert=True)
        return
    [msg, total], pic = result
    totalpg, kek = divmod(total, 15)
    if kek != 0:
        totalpg + 1
    button = []
    if total > 15:
        nex = f"{req}_{idm}_{int(reqpg)+1}_{qry}_{pg}_{auth}_{user}"
        bac = f"{req}_{idm}_{int(reqpg)-1}_{qry}_{pg}_{auth}_{user}"
        if int(reqpg) == 0:
            button.append([InlineKeyboardButton(text="NEXT", callback_data=nex)])
        elif int(reqpg) == totalpg:
            button.append([InlineKeyboardButton(text="BACK", callback_data=bac)])
        else:
            button.append(
                [
                    InlineKeyboardButton(text="BACK", callback_data=bac),
                    InlineKeyboardButton(text="NEXT", callback_data=nex),
                ]
            )
    button.append(
        [
            InlineKeyboardButton(
                text=f"{bt}", callback_data=f"{reqb}_{idm}_0_{qry}_{pg}_{auth}_{user}"
            )
        ]
    )
    button.append(
        [
            InlineKeyboardButton(
                text="BACK", callback_data=f"page_CHARACTER_{qry}_{pg}_{auth}_{user}"
            )
        ]
    )
    try:
        await cq.edit_message_media(
            InputMediaPhoto(pic, caption=msg), reply_markup=InlineKeyboardMarkup(button)
        )
    except (WebpageMediaEmpty, WebpageCurlFailed):
        await clog("Mikobot", pic, "LINK", msg=cq)
        await cq.edit_message_media(
            InputMediaPhoto(failed_pic, caption=msg),
            reply_markup=InlineKeyboardMarkup(button),
        )


headlines_text = """
Turn LiveChart option on to get news feeds from livechart.me
Turn MyAnimeList option on to get news feeds from myanimelist.net

For Auto Pin and Auto Unpin features, give the bot "Pin Message" and "Delete Message" perms
Auto Unpin can be customized, click on the button to see available options
"""


@app.on_callback_query(filters.regex(pattern=r"headlines_(.*)"))
async def headlines_btn(client: Client, cq: CallbackQuery):
    cus = cq.from_user.id
    qry = cq.data.split("_")[1]
    gid = int(cq.data.split("_")[2])
    try:
        k = (await client.get_chat_member(gid, cus)).status
    except UserNotParticipant:
        await cq.answer()
        return
    if cus not in BOT_OWNER and k == MEMBER:
        await cq.answer(
            "You don't have enough permissions to change this!!!", show_alert=True
        )
        return
    lcdata = await HD.find_one({"_id": gid})
    maldata = await MHD.find_one({"_id": gid})
    lchd = "LiveChart: OFF"
    malhd = "MyAnimeList: OFF"
    malhdpin = lchdpin = "Auto Pin: OFF"
    malpin = lcpin = None
    if lcdata:
        lchd = "LiveChart: ON"
        try:
            lcpin = lcdata["pin"]
            lchdpin = f"Auto Pin: {lcpin}"
        except KeyError:
            pass
    if maldata:
        malhd = "MyAnimeList: ON"
        try:
            malpin = maldata["pin"]
            malhdpin = f"Auto Pin: {malpin}"
        except KeyError:
            pass
    if "mal" in qry:
        data = maldata
        pin = malpin
        pin_msg = malhdpin
        collection = MHD
        src_status = malhd
        srcname = "MyAnimeList"
    else:
        data = lcdata
        pin = lcpin
        pin_msg = lchdpin
        collection = HD
        src_status = lchd
        srcname = "LiveChart"
    if re.match(r"^(mal|lc)hd$", qry):
        if data:
            await collection.find_one_and_delete(data)
            src_status = f"{srcname}: OFF"
            pin_msg = f"Auto Pin: OFF"
        else:
            await collection.insert_one({"_id": gid})
            src_status = f"{srcname}: ON"
            pin_msg = f"Auto Pin: OFF"
    if re.match(r"^(mal|lc)hdpin$", qry):
        if data:
            if pin:
                switch = "ON" if pin == "OFF" else "OFF"
                await collection.find_one_and_update(
                    data, {"$set": {"pin": switch, "unpin": None}}, upsert=True
                )
                pin_msg = f"Auto Pin: {switch}"
            else:
                await collection.find_one_and_update(
                    data, {"$set": {"pin": "ON"}}, upsert=True
                )
                pin_msg = f"Auto Pin: ON"
        else:
            await cq.answer(f"Please enable {srcname} first!!!", show_alert=True)
    if "mal" in qry:
        malhdpin = pin_msg
        malhd = src_status
    else:
        lchdpin = pin_msg
        lchd = src_status
    btn = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(text=lchd, callback_data=f"headlines_lchd_{gid}")],
            [
                InlineKeyboardButton(
                    text=lchdpin, callback_data=f"headlines_lchdpin_{gid}"
                ),
                InlineKeyboardButton(
                    text="Auto Unpin (LC)", callback_data=f"anpin_call_lc_{gid}"
                ),
            ],
            [InlineKeyboardButton(text=malhd, callback_data=f"headlines_malhd_{gid}")],
            [
                InlineKeyboardButton(
                    text=malhdpin, callback_data=f"headlines_malhdpin_{gid}"
                ),
                InlineKeyboardButton(
                    text="Auto Unpin (MAL)", callback_data=f"anpin_call_mal_{gid}"
                ),
            ],
            [InlineKeyboardButton(text="BACK", callback_data=f"settogl_call_{gid}")],
        ]
    )
    await cq.edit_message_text(headlines_text, reply_markup=btn)
    await cq.answer()


TIMES = {
    "1 day": 86400,
    "5 days": 432000,
    "1 week": 604800,
    "2 week": 1209600,
    "1 month": 2592000,
    "New Feed": 0,
    "OFF": None,
}


@app.on_callback_query(filters.regex(pattern=r"anpin_(.*)"))
async def auto_unpin(client: Client, cq: CallbackQuery):
    cus = cq.from_user.id
    qry = cq.data.split("_")[1]
    src = cq.data.split("_")[2]
    gid = int(cq.data.split("_")[3])
    try:
        k = (await client.get_chat_member(gid, cus)).status
    except UserNotParticipant:
        await cq.answer()
        return
    if cus not in BOT_OWNER and k == MEMBER:
        await cq.answer(
            "You don't have enough permissions to change this!!!", show_alert=True
        )
        return
    cancel = False
    if src == "lc":
        srcname = "LiveChart"
        collection = HD
    else:
        srcname = "MyAnimeList"
        collection = MHD
    data = await collection.find_one({"_id": gid})
    if data:
        try:
            data["pin"]
            try:
                unpin = data["unpin"]
            except KeyError:
                unpin = None
        except KeyError:
            cancel = True
    else:
        cancel = True
    if cancel:
        return await cq.answer(
            f"Please enable {srcname} and Auto Pin option for them!!!", show_alert=True
        )
    setting = None
    if qry == "call":
        pass
    elif qry == "None":
        setting = {"unpin": None}
    elif qry.isdigit():
        if int(qry) == 0:
            unpin = int(qry)
            setting = {"unpin": 0}
        else:
            now = round(time.time(), -2)
            unpin = int(qry)
            setting = {"unpin": int(qry), "next_unpin": int(qry) + int(now)}
    if setting:
        await collection.find_one_and_update(data, {"$set": setting})
    btn = []
    row = []
    count = 0
    for i in TIMES.keys():
        count = count + 1
        row.append(
            InlineKeyboardButton(i, callback_data=f"unpin_{TIMES[i]}_{src}_{gid}")
        )
        if count == 3:
            btn.append(row)
            count = 0
            row = []
    if len(row) != 0:
        btn.append(row)
    btn.append([InlineKeyboardButton("BACK", callback_data=f"headlines_call_{gid}")])
    if type(unpin) is int:
        if unpin == 0:
            unpindata = "after Next Feed"
        else:
            unpindata = "after " + list(TIMES.keys())[list(TIMES.values()).index(unpin)]
    else:
        unpindata = "OFF"
    await cq.edit_message_text(
        f"Auto Unpin options for {srcname}\nCurrently set to: {unpindata}",
        reply_markup=InlineKeyboardMarkup(btn),
    )
    await cq.answer()


BULLETS = ["➤", "•", "⚬", "▲", "▸", "△", "⋟", "»", "None"]


@app.on_callback_query(filters.regex(pattern=r"cui_(.*)"))
async def change_ui_btn(client: Client, cq: CallbackQuery):
    cus = cq.from_user.id
    qry = cq.data.split("_")[1]
    gid = cq.data.split("_")[2]
    try:
        k = (await client.get_chat_member(gid, cus)).status
    except UserNotParticipant:
        await cq.answer()
        return
    if cus not in BOT_OWNER and k == MEMBER:
        await cq.answer(
            "You don't have enough permissions to change this!!!", show_alert=True
        )
        return
    await cq.answer()
    row, btn = [], []
    for i in BULLETS:
        row.append(InlineKeyboardButton(text=i, callback_data=f"cui_{i}_{gid}"))
        if len(row) == 3:
            btn.append(row)
            row = []
    btn.append(row)
    btn.append(
        [
            InlineKeyboardButton(text="CAPS", callback_data=f"cui_Caps_{gid}"),
            InlineKeyboardButton(text="UPPER", callback_data=f"cui_UPPER_{gid}"),
        ]
    )
    btn.append([InlineKeyboardButton(text="BACK", callback_data=f"settogl_call_{gid}")])
    if qry in ["Caps", "UPPER"]:
        if await GUI.find_one({"_id": gid}):
            await GUI.update_one({"_id": gid}, {"$set": {"cs": qry}})
        else:
            await GUI.insert_one({"_id": gid, "bl": "➤", "cs": qry})
    elif qry != "call":
        bullet = qry
        if qry == "None":
            bullet = None
        if await GUI.find_one({"_id": gid}):
            await GUI.update_one({"_id": gid}, {"$set": {"bl": bullet}})
        else:
            await GUI.insert_one({"_id": gid, "bl": bullet, "cs": "UPPER"})
    bl = "➤"
    cs = "UPPER"
    if await GUI.find_one({"_id": gid}):
        data = await GUI.find_one({"_id": gid})
        bl = data["bl"]
        cs = data["cs"]
    text = f"""Selected bullet in this group: {bl}
Selected text case in this group: {cs}"""
    await cq.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btn))


## For accepting commands from edited messages


@app.on_edited_message(
    filters.command(["anime", f"anime{BOT_USERNAME}"], prefixes=PREFIX_HANDLER)
)
async def anime_edit_cmd(client: app, message: Message):
    await anime_cmd(client, message)


@app.on_edited_message(
    filters.command(["manga", f"manga{BOT_USERNAME}"], prefixes=PREFIX_HANDLER)
)
async def manga_edit_cmd(client: app, message: Message):
    await manga_cmd(client, message)


@app.on_edited_message(
    filters.command(["character", f"character{BOT_USERNAME}"], prefixes=PREFIX_HANDLER)
)
async def character_edit_cmd(client: app, message: Message):
    await character_cmd(client, message)


@app.on_edited_message(
    filters.command(["anilist", f"anilist{BOT_USERNAME}"], prefixes=PREFIX_HANDLER)
)
async def anilist_edit_cmd(client: app, message: Message):
    await anilist_cmd(client, message)


@app.on_edited_message(
    filters.command(["top", f"top{BOT_USERNAME}"], prefixes=PREFIX_HANDLER)
)
async def top_edit_cmd(client: app, message: Message):
    await top_tags_cmd(client, message)


@app.on_edited_message(
    filters.command(["airing", f"airing{BOT_USERNAME}"], prefixes=PREFIX_HANDLER)
)
async def airing_edit_cmd(client: app, message: Message):
    await airing_cmd(client, message)


@app.on_edited_message(
    ~filters.private
    & filters.command(
        ["anisettings", f"anisettings{BOT_USERNAME}"], prefixes=PREFIX_HANDLER
    )
)
async def settings_edit_cmd(client: app, message: Message):
    await settings_cmd(client, message)


@app.on_edited_message(
    filters.command(["browse", f"browse{BOT_USERNAME}"], prefixes=PREFIX_HANDLER)
)
async def browse_edit_cmd(client: app, message: Message):
    await browse_cmd(client, message)


@app.on_edited_message(
    filters.command(
        ["gettags", f"gettags{BOT_USERNAME}", "getgenres", f"getgenres{BOT_USERNAME}"],
        prefixes=PREFIX_HANDLER,
    )
)
async def tags_genres_edit_cmd(client: app, message: Message):
    await list_tags_genres_cmd(client, message)


@app.on_message(
    filters.command(["studio", f"studio{BOT_USERNAME}"], prefixes=PREFIX_HANDLER)
)
async def studio_edit_cmd(client: Client, message: Message):
    await studio_cmd(client, message)


@app.on_message(
    filters.command(["schedule", f"schedule{BOT_USERNAME}"], prefixes=PREFIX_HANDLER)
)
@control_user
async def get_schuled(client: Client, message: Message, mdata: dict):
    """Get List of Scheduled Anime"""
    gid = mdata["chat"]["id"]
    find_gc = await DC.find_one({"_id": gid})
    if find_gc is not None and "schedule" in find_gc["cmd_list"].split():
        return
    x = await client.send_message(gid, "<code>Fetching Scheduled Animes</code>")
    try:
        user = mdata["from_user"]["id"]
    except KeyError:
        user = mdata["sender_chat"]["id"]
    msg = await get_scheduled()
    buttons = get_btns("SCHEDULED", result=[msg[1]], user=user)
    await x.edit_text(msg[0], reply_markup=buttons)


@app.on_callback_query(filters.regex(pattern=r"sched_(.*)"))
@check_user
async def ns_(client: app, cq: CallbackQuery, cdata: dict):
    kek, day, user = cdata["data"].split("_")
    msg = await get_scheduled(int(day))
    buttons = get_btns("SCHEDULED", result=[int(day)], user=user)
    await cq.edit_message_text(msg[0], reply_markup=buttons)


@app.on_edited_message(
    filters.command(["schedule", f"schedule{BOT_USERNAME}"], prefixes=PREFIX_HANDLER)
)
async def get_schuled_edit(client: Client, message: Message):
    await get_schuled(client, message)


@app.on_message(
    filters.command(["watch", f"watch{BOT_USERNAME}"], prefixes=PREFIX_HANDLER)
)
@control_user
async def get_watch_order(client: Client, message: Message, mdata: dict):
    """Get List of Scheduled Anime"""
    gid = mdata["chat"]["id"]
    find_gc = await DC.find_one({"_id": gid})
    if find_gc is not None and "watch" in find_gc["cmd_list"].split():
        return
    x = message.text.split(" ", 1)
    if len(x) == 1:
        await message.reply_text("Nothing given to search for!!!")
        return
    try:
        user = mdata["from_user"]["id"]
    except KeyError:
        user = mdata["sender_chat"]["id"]
    data = get_wols(x[1])
    msg = f"Found related animes for the query {x[1]}"
    buttons = []
    if data == []:
        await client.send_message(gid, "No results found!!!")
        return
    for i in data:
        buttons.append(
            [
                InlineKeyboardButton(
                    str(i[1]), callback_data=f"watch_{i[0]}_{x[1]}_0_{user}"
                )
            ]
        )
    await client.send_message(gid, msg, reply_markup=InlineKeyboardMarkup(buttons))


@app.on_callback_query(filters.regex(pattern=r"watch_(.*)"))
@check_user
async def watch_(client: app, cq: CallbackQuery, cdata: dict):
    kek, id_, qry, req, user = cdata["data"].split("_")
    msg, total = get_wo(int(id_), int(req))
    totalpg, lol = divmod(total, 50)
    button = []
    if lol != 0:
        totalpg + 1
    if total > 50:
        if int(req) == 0:
            button.append(
                [
                    InlineKeyboardButton(
                        text="NEXT",
                        callback_data=f"{kek}_{id_}_{qry}_{int(req)+1}_{user}",
                    )
                ]
            )
        elif int(req) == totalpg:
            button.append(
                [
                    InlineKeyboardButton(
                        text="PREV",
                        callback_data=f"{kek}_{id_}_{qry}_{int(req)-1}_{user}",
                    )
                ]
            )
        else:
            button.append(
                [
                    InlineKeyboardButton(
                        text="PREV",
                        callback_data=f"{kek}_{id_}_{qry}_{int(req)-1}_{user}",
                    ),
                    InlineKeyboardButton(
                        text="NEXT",
                        callback_data=f"{kek}_{id_}_{qry}_{int(req)+1}_{user}",
                    ),
                ]
            )
    button.append([InlineKeyboardButton("Back", callback_data=f"wol_{qry}_{user}")])
    await cq.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(button))


@app.on_callback_query(filters.regex(pattern=r"wol_(.*)"))
@check_user
async def wls(client: app, cq: CallbackQuery, cdata: dict):
    kek, qry, user = cdata["data"].split("_")
    data = get_wols(qry)
    msg = f"Found related animes for the query {qry}"
    buttons = []
    for i in data:
        buttons.append(
            [
                InlineKeyboardButton(
                    str(i[1]), callback_data=f"watch_{i[0]}_{qry}_0_{user}"
                )
            ]
        )
    await cq.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(buttons))


@app.on_edited_message(
    filters.command(["watch", f"watch{BOT_USERNAME}"], prefixes=PREFIX_HANDLER)
)
async def get_watch_order_edit(client: Client, message: Message):
    await get_watch_order(client, message)


@app.on_message(
    filters.command(["fillers", f"fillers{BOT_USERNAME}"], prefixes=PREFIX_HANDLER)
)
@control_user
async def fillers_cmd(client: app, message: Message, mdata: dict):
    find_gc = await DC.find_one({"_id": mdata["chat"]["id"]})
    try:
        user = mdata["from_user"]["id"]
    except KeyError:
        user = mdata["sender_chat"]["id"]
    if find_gc is not None and "watch" in find_gc["cmd_list"].split():
        return
    qry = mdata["text"].split(" ", 1)
    if len(qry) == 1:
        return await message.reply_text(
            """Give some anime name to search fillers for
example: /fillers Detective Conan"""
        )
    k = search_filler(qry[1])
    if k == {}:
        await message.reply_text("No fillers found for the given anime...")
        return
    button = []
    list_ = list(k.keys())
    if len(list_) == 1:
        result = parse_filler(k.get(list_[0]))
        msg = ""
        msg += f"Fillers for anime `{list_[0]}`\n\nManga Canon episodes:\n"
        msg += str(result.get("total_ep"))
        msg += "\n\nMixed/Canon fillers:\n"
        msg += str(result.get("mixed_ep"))
        msg += "\n\nFillers:\n"
        msg += str(result.get("filler_ep"))
        if result.get("ac_ep") is not None:
            msg += "\n\nAnime Canon episodes:\n"
            msg += str(result.get("ac_ep"))
        await message.reply_text(msg)
        return
    for i in list_:
        fl_js = rand_key()
        FILLERS[fl_js] = [k.get(i), i]
        button.append([InlineKeyboardButton(i, callback_data=f"fill_{fl_js}_{user}")])
    await message.reply_text(
        "Pick anime you want to see fillers list for:",
        reply_markup=InlineKeyboardMarkup(button),
    )


@app.on_callback_query(filters.regex(pattern=r"fill_(.*)"))
@check_user
async def filler_btn(client: app, cq: CallbackQuery, cdata: dict):
    kek, req, user = cdata["data"].split("_")
    result = parse_filler((FILLERS.get(req))[0])
    msg = ""
    msg += f"**Fillers for anime** `{(FILLERS.get(req))[1]}`"
    msg += "\n\n**Manga Canon episodes:**\n"
    msg += str(result.get("total_ep"))
    msg += "\n\n**Mixed/Canon fillers:**\n"
    msg += str(result.get("mixed_ep"))
    msg += "\n\n**Fillers:**\n"
    msg += str(result.get("filler_ep"))
    if result.get("ac_ep") is not None:
        msg += "\n\n**Anime Canon episodes:**\n"
        msg += str(result.get("ac_ep"))
    await cq.edit_message_text(msg)


@app.on_message(
    filters.command(["fillers", f"fillers{BOT_USERNAME}"], prefixes=PREFIX_HANDLER)
)
async def fillers_cmd(client: app, message: Message):
    await fillers_cmd(client, message)


@app.on_message(filters.command("animequotes"))
async def animequotes(client, message):
    name = (
        message.reply_to_message.from_user.first_name
        if message.reply_to_message
        else message.from_user.first_name
    )
    keyboard = [[InlineKeyboardButton(text="CHANGE", callback_data="changek_quote")]]
    await message.reply_photo(
        photo=random.choice(QUOTES_IMG),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


@app.on_callback_query(filters.regex("changek_quote"))
async def changek_quote(client, callback_query):
    keyboard = [[InlineKeyboardButton(text="CHANGE", callback_data="changek_quote")]]
    await callback_query.edit_message_media(
        media=InputMediaPhoto(media=random.choice(QUOTES_IMG)),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


QUOTES_IMG = [
    "https://i.imgur.com/Iub4RYj.jpg",
    "https://i.imgur.com/uvNMdIl.jpg",
    "https://i.imgur.com/YOBOntg.jpg",
    "https://i.imgur.com/fFpO2ZQ.jpg",
    "https://i.imgur.com/f0xZceK.jpg",
    "https://i.imgur.com/RlVcCip.jpg",
    "https://i.imgur.com/CjpqLRF.jpg",
    "https://i.imgur.com/8BHZDk6.jpg",
    "https://i.imgur.com/8bHeMgy.jpg",
    "https://i.imgur.com/5K3lMvr.jpg",
    "https://i.imgur.com/NTzw4RN.jpg",
    "https://i.imgur.com/wJxryAn.jpg",
    "https://i.imgur.com/9L0DWzC.jpg",
    "https://i.imgur.com/sBe8TTs.jpg",
    "https://i.imgur.com/1Au8gdf.jpg",
    "https://i.imgur.com/28hFQeU.jpg",
    "https://i.imgur.com/Qvc03JY.jpg",
    "https://i.imgur.com/gSX6Xlf.jpg",
    "https://i.imgur.com/iP26Hwa.jpg",
    "https://i.imgur.com/uSsJoX8.jpg",
    "https://i.imgur.com/OvX3oHB.jpg",
    "https://i.imgur.com/JMWuksm.jpg",
    "https://i.imgur.com/lhM3fib.jpg",
    "https://i.imgur.com/64IYKkw.jpg",
    "https://i.imgur.com/nMbyA3J.jpg",
    "https://i.imgur.com/7KFQhY3.jpg",
    "https://i.imgur.com/mlKb7zt.jpg",
    "https://i.imgur.com/JCQGJVw.jpg",
    "https://i.imgur.com/hSFYDEz.jpg",
    "https://i.imgur.com/PQRjAgl.jpg",
    "https://i.imgur.com/ot9624U.jpg",
    "https://i.imgur.com/iXmqN9y.jpg",
    "https://i.imgur.com/RhNBeGr.jpg",
    "https://i.imgur.com/tcMVNa8.jpg",
    "https://i.imgur.com/LrVg810.jpg",
    "https://i.imgur.com/TcWfQlz.jpg",
    "https://i.imgur.com/muAUdvJ.jpg",
    "https://i.imgur.com/AtC7ZRV.jpg",
    "https://i.imgur.com/sCObQCQ.jpg",
    "https://i.imgur.com/AJFDI1r.jpg",
    "https://i.imgur.com/TCgmRrH.jpg",
    "https://i.imgur.com/LMdmhJU.jpg",
    "https://i.imgur.com/eyyax0N.jpg",
    "https://i.imgur.com/YtYxV66.jpg",
    "https://i.imgur.com/292w4ye.jpg",
    "https://i.imgur.com/6Fm1vdw.jpg",
    "https://i.imgur.com/2vnBOZd.jpg",
    "https://i.imgur.com/j5hI9Eb.jpg",
    "https://i.imgur.com/cAv7pJB.jpg",
    "https://i.imgur.com/jvI7Vil.jpg",
    "https://i.imgur.com/fANpjsg.jpg",
    "https://i.imgur.com/5o1SJyo.jpg",
    "https://i.imgur.com/dSVxmh8.jpg",
    "https://i.imgur.com/02dXlAD.jpg",
    "https://i.imgur.com/htvIoGY.jpg",
    "https://i.imgur.com/hy6BXOj.jpg",
    "https://i.imgur.com/OuwzNYu.jpg",
    "https://i.imgur.com/L8vwvc2.jpg",
    "https://i.imgur.com/3VMVF9y.jpg",
    "https://i.imgur.com/yzjq2n2.jpg",
    "https://i.imgur.com/0qK7TAN.jpg",
    "https://i.imgur.com/zvcxSOX.jpg",
    "https://i.imgur.com/FO7bApW.jpg",
    "https://i.imgur.com/KK06gwg.jpg",
    "https://i.imgur.com/6lG4tsO.jpg",
]


# <================================================= HELP ======================================================>
__help__ = """
⛩ *Anime:*

➠ *Dazai provides you the best anime-based commands including anime news and much more!*

➠ *Commands:*

» /anime: fetches info on single anime (includes buttons to look up for prequels and sequels)
» /character: fetches info on multiple possible characters related to query
» /manga: fetches info on multiple possible mangas related to query
» /airing: fetches info on airing data for anime
» /studio: fetches info on multiple possible studios related to query
» /schedule: fetches scheduled animes
» /browse: get popular, trending or upcoming animes

➠ /animequotes: get random anime quotes

» /anisettings: to toggle NSFW lock and airing notifications and other settings in groups (anime news)
» /top: to retrieve top animes for a genre or tag
» /watch: fetches watch order for anime series
» /fillers: to get a list of anime fillers
» /gettags: get a list of available tags
» /getgenres - Get list of available Genres
"""

__mod_name__ = "ANIME"
# <================================================== END =====================================================>
