import codecs
import pickle
from typing import List

from Database.mongodb.db import dbname

blacklist_filtersdb = dbname.blacklistFilters


def obj_to_str(obj):
    if not obj:
        return False
    string = codecs.encode(pickle.dumps(obj), "base64").decode()
    return string


def str_to_obj(string: str):
    obj = pickle.loads(codecs.decode(string.encode(), "base64"))
    return obj


async def get_blacklisted_words(chat_id: int) -> List[str]:
    _filters = await blacklist_filtersdb.find_one({"chat_id": chat_id})
    if not _filters:
        return []
    return _filters["filters"]


async def save_blacklist_filter(chat_id: int, word: str):
    word = word.lower().strip()
    _filters = await get_blacklisted_words(chat_id)
    _filters.append(word)
    await blacklist_filtersdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"filters": _filters}},
        upsert=True,
    )


async def delete_blacklist_filter(chat_id: int, word: str) -> bool:
    filtersd = await get_blacklisted_words(chat_id)
    word = word.lower().strip()
    if word in filtersd:
        filtersd.remove(word)
        await blacklist_filtersdb.update_one(
            {"chat_id": chat_id},
            {"$set": {"filters": filtersd}},
            upsert=True,
        )
        return True
    return False
