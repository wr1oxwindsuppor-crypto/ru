import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

from config import ADMIN_IDS, BOT_TOKEN
from database import init_db
from handlers.admin import router as admin_router
from handlers.user import router as user_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [BotCommand(command="start", description="Запустить бота")],
        scope=BotCommandScopeDefault(),
    )

    admin_commands = [
        BotCommand(command="addcode", description="Добавить код (фото+видео)"),
        BotCommand(command="delcode", description="Удалить код"),
        BotCommand(command="stats", description="Статистика"),
        BotCommand(command="addch", description="Добавить канал"),
        BotCommand(command="delch", description="Удалить канал"),
        BotCommand(command="ch", description="Список каналов"),
    ]
    for admin_id in ADMIN_IDS:
        try:
            await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=admin_id))
        except Exception as exc:  # noqa: BLE001 — не критично, продолжаем запуск
            logger.warning("Не удалось задать меню команд для админа %s: %s", admin_id, exc)


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан. Проверьте переменные окружения (.env).")
    if not ADMIN_IDS:
        logger.warning("ADMIN_IDS не задан — админ-команды будут недоступны никому.")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Роутер админа подключаем первым, чтобы его команды обрабатывались в приоритете.
    dp.include_router(admin_router)
    dp.include_router(user_router)

    await init_db()
    await setup_commands(bot)

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Бот запущен, начинаю polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
