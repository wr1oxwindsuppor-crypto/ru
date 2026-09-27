from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

import database as db
from config import NO_ADS_MESSAGE
from keyboards import subscription_keyboard, watch_keyboard

router = Router(name="user")

ASK_CODE = "🎬 Отправьте код фильма (3 цифры), и я найду его для вас."
CODE_NOT_FOUND = "❌ Фильм с таким кодом не найден.\nПроверьте код и отправьте ещё раз."
NOT_A_CODE = "🔢 Пожалуйста, отправьте код из 3 цифр (например: 123)."
SUB_REQUIRED_TEXT = (
    "Чтобы пользоваться ботом, подпишитесь на канал(ы) ниже, "
    "затем нажмите «✅ Проверить»:"
)
STILL_NOT_SUBSCRIBED = "❗️ Вы ещё не подписались на все каналы."


async def get_unsubscribed_channels(bot: Bot, user_id: int) -> list:
    channels = await db.list_channels()
    unsubscribed = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch["chat_id"], user_id=user_id)
            if member.status in ("left", "kicked"):
                unsubscribed.append(ch)
        except Exception:
            # Бот не состоит в канале / нет прав / канал недоступен —
            # пропускаем проверку по этому каналу, чтобы не блокировать пользователя.
            continue
    return unsubscribed


async def send_welcome_body(message: Message) -> None:
    if await db.count_codes() == 0:
        await message.answer(NO_ADS_MESSAGE)
    else:
        await message.answer(ASK_CODE)


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot) -> None:
    await db.touch_user(message.from_user.id)
    unsubscribed = await get_unsubscribed_channels(bot, message.from_user.id)
    if unsubscribed:
        await message.answer(SUB_REQUIRED_TEXT, reply_markup=subscription_keyboard(unsubscribed))
        return
    await send_welcome_body(message)


@router.callback_query(F.data == "check_sub")
async def cb_check_sub(callback: CallbackQuery, bot: Bot) -> None:
    unsubscribed = await get_unsubscribed_channels(bot, callback.from_user.id)
    if unsubscribed:
        await callback.answer(STILL_NOT_SUBSCRIBED, show_alert=True)
        return
    await callback.answer()
    await callback.message.delete()
    await send_welcome_body(callback.message)


@router.message(F.text.regexp(r"^\d{3}$"))
async def handle_code(message: Message, bot: Bot) -> None:
    await db.touch_user(message.from_user.id)
    unsubscribed = await get_unsubscribed_channels(bot, message.from_user.id)
    if unsubscribed:
        await message.answer(SUB_REQUIRED_TEXT, reply_markup=subscription_keyboard(unsubscribed))
        return

    code = message.text.strip()
    entry = await db.get_code(code)
    await db.log_search(message.from_user.id, code, found=entry is not None)

    if not entry:
        await message.answer(CODE_NOT_FOUND)
        return

    await db.increment_hits(code)
    await message.answer_photo(
        entry["photo_file_id"],
        caption=f"🎬 {entry['movie_name']}",
        reply_markup=watch_keyboard(code),
    )


@router.callback_query(F.data.startswith("watch:"))
async def cb_watch(callback: CallbackQuery, bot: Bot) -> None:
    code = callback.data.split(":", 1)[1]

    unsubscribed = await get_unsubscribed_channels(bot, callback.from_user.id)
    if unsubscribed:
        await callback.answer(STILL_NOT_SUBSCRIBED, show_alert=True)
        return

    entry = await db.get_code(code)
    if not entry or not entry.get("film_file_id"):
        await callback.answer("⏳ Этот фильм ещё не загружен.", show_alert=True)
        return

    await callback.answer()
    if entry["film_type"] == "document":
        await callback.message.answer_document(entry["film_file_id"])
    else:
        await callback.message.answer_video(entry["film_file_id"])


@router.message(F.text & ~F.text.startswith("/"))
async def handle_other_text(message: Message) -> None:
    await message.answer(NOT_A_CODE)
