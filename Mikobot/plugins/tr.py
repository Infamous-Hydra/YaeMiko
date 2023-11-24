# <============================================== IMPORTS =========================================================>
import json
import random
import re
from urllib.parse import quote

import requests
import urllib3
from emoji import EMOJI_DATA
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, filters

from Mikobot import LOGGER, function
from Mikobot.plugins.anime import DEFAULT_SERVICE_URLS, LANGUAGES
from Mikobot.plugins.disable import DisableAbleCommandHandler
from Mikobot.plugins.helper_funcs.chat_status import check_admin

# <=======================================================================================================>

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URLS_SUFFIX = [
    re.search("translate.google.(.*)", url.strip()).group(1)
    for url in DEFAULT_SERVICE_URLS
]
URL_SUFFIX_DEFAULT = "com"


# <================================================ FUNCTION =======================================================>
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

    def __init__(self, url_suffix="com", timeout=5, proxies=None):
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
        except:
            lang_src = "auto"
        try:
            lang = LANGUAGES[lang_tgt]
        except:
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
            if self.proxies == None or type(self.proxies) != dict:
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
                                if pronounce == False:
                                    return sentences
                                elif pronounce == True:
                                    return [sentences, None, None]
                            translate_text = ""
                            for sentence in sentences:
                                sentence = sentence[0]
                                translate_text += sentence.strip() + " "
                            translate_text = translate_text
                            if pronounce == False:
                                return translate_text
                            elif pronounce == True:
                                pronounce_src = response_[0][0]
                                pronounce_tgt = response_[1][0][0][1]
                                return [translate_text, pronounce_src, pronounce_tgt]
                        elif len(response) == 2:
                            sentences = []
                            for i in response:
                                sentences.append(i[0])
                            if pronounce == False:
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
            return LOGGER.debug("Warning: Can only detect less than 5000 characters")
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
            if self.proxies == None or type(self.proxies) != dict:
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
            LOGGER.debug(str(e))
            raise google_new_transError(tts=self, response=r)
        except requests.exceptions.RequestException as e:
            # Request failed
            LOGGER.debug(str(e))
            raise google_new_transError(tts=self)


@check_admin(is_user=True)
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message

    if message.reply_to_message:
        await message.reply_to_message.reply_text(
            args[1],
            parse_mode="MARKDOWN",
            disable_web_page_preview=True,
        )
    else:
        await message.reply_text(
            args[1],
            quote=False,
            parse_mode="MARKDOWN",
            disable_web_page_preview=True,
        )
    await message.delete()


async def totranslate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    problem_lang_code = []
    for key in LANGUAGES:
        if "-" in key:
            problem_lang_code.append(key)

    try:
        if (
            message.reply_to_message
            and not message.reply_to_message.forum_topic_created
        ):
            args = update.effective_message.text.split(None, 1)
            if message.reply_to_message.text:
                text = message.reply_to_message.text
            elif message.reply_to_message.caption:
                text = message.reply_to_message.caption

            try:
                source_lang = args[1].split(None, 1)[0]
            except (IndexError, AttributeError):
                source_lang = "en"

        else:
            args = update.effective_message.text.split(None, 2)
            text = args[2]
            source_lang = args[1]

        if source_lang.count("-") == 2:
            for lang in problem_lang_code:
                if lang in source_lang:
                    if source_lang.startswith(lang):
                        dest_lang = source_lang.rsplit("-", 1)[1]
                        source_lang = source_lang.rsplit("-", 1)[0]
                    else:
                        dest_lang = source_lang.split("-", 1)[1]
                        source_lang = source_lang.split("-", 1)[0]
        elif source_lang.count("-") == 1:
            for lang in problem_lang_code:
                if lang in source_lang:
                    dest_lang = source_lang
                    source_lang = None
                    break
            if dest_lang is None:
                dest_lang = source_lang.split("-")[1]
                source_lang = source_lang.split("-")[0]
        else:
            dest_lang = source_lang
            source_lang = None

        exclude_list = EMOJI_DATA.keys()
        for emoji in exclude_list:
            if emoji in text:
                text = text.replace(emoji, "")

        trl = google_translator()
        if source_lang is None:
            detection = trl.detect(text)
            trans_str = trl.translate(text, lang_tgt=dest_lang)
            return await message.reply_text(
                f"📒 *Translated from* `{detection[0]}` to `{dest_lang}`:\n`{trans_str}`",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            trans_str = trl.translate(text, lang_tgt=dest_lang, lang_src=source_lang)
            await message.reply_text(
                f"📒 *Translated from* `{source_lang}` to `{dest_lang}`:\n`{trans_str}`",
                parse_mode=ParseMode.MARKDOWN,
            )

    except IndexError:
        await update.effective_message.reply_text(
            "Reply to messages or write messages from other languages ​​for translating into the intended language\n\n"
            "Example: `/tr en-ta` to translate from English to Tamil\n"
            "Or use: `/tr ta` for automatic detection and translating it into Tamil.\n"
            "See [List of Language Codes](https://t.me/Hydra_Updates/80) for a list of language codes.",
            parse_mode="markdown",
            disable_web_page_preview=True,
        )
    except ValueError:
        await update.effective_message.reply_text("The intended language is not found!")
    else:
        return


# <=================================================== HELP ====================================================>


__help__ = """
➠ `/tr` or `/tl` (language code) as reply to a long message

➠ *Example:*

» `/tr en`*:* translates something to english

» `/tr hi-en`*:* translates hindi to english

» /echo < text >: echos the message.
"""

TRANSLATE_HANDLER = DisableAbleCommandHandler(["tr", "tl"], totranslate, block=False)
ECHO_HANDLER = DisableAbleCommandHandler(
    "echo", echo, filters=filters.ChatType.GROUPS, block=False
)

function(TRANSLATE_HANDLER)
function(ECHO_HANDLER)

__mod_name__ = "TRANSLATOR"
__command_list__ = ["tr", "tl", "echo"]
__handlers__ = [TRANSLATE_HANDLER]
# <================================================ END =======================================================>
