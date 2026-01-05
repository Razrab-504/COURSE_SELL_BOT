from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

ADMIN_ID = int(os.getenv("ADMIN_ID"))

from src.db.session import LocalSession
from src.db.crud.users import get_user_by_telegram

class IsUser(BaseFilter):
    async def __call__(self, events: Message | CallbackQuery) -> bool:
        if events.from_user.id == ADMIN_ID:
            return False

        async with LocalSession() as db:
            user = await get_user_by_telegram(db, events.from_user.id)
            if not user:
                return True
            return not getattr(user, "is_banned", False)