from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv, find_dotenv
import os
import asyncio

from src.bot.handlers.user_handlers import user_router
from src.bot.handlers.admin_handlers import admin_router

# ensure ORM models are imported and registered in metadata at app startup
import src.db.models.users
import src.db.models.courses
import src.db.models.purchases

load_dotenv(find_dotenv())

bot = Bot(token=os.getenv("BOT_TOKEN"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

async def main():
    dp.include_routers(user_router, admin_router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot Stoped!")