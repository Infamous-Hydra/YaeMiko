from Database.mongodb.db import dbname

collection = dbname["whisper"]


class Whispers:
    @staticmethod
    async def add_whisper(WhisperId, WhisperData):
        whisper = {"WhisperId": WhisperId, "whisperData": WhisperData}
        await collection.insert_one(whisper)

    @staticmethod
    async def del_whisper(WhisperId):
        await collection.delete_one({"WhisperId": WhisperId})

    @staticmethod
    async def get_whisper(WhisperId):
        whisper = await collection.find_one({"WhisperId": WhisperId})
        return whisper["whisperData"] if whisper else None
