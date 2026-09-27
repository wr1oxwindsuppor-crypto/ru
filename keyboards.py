from typing import Dict, List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def subscription_keyboard(channels: List[Dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ch in channels:
        title = ch.get("title") or "Канал"
        url = ch.get("url")
        if url:
            builder.row(InlineKeyboardButton(text=f"📢 {title}", url=url))
    builder.row(InlineKeyboardButton(text="✅ Проверить", callback_data="check_sub"))
    return builder.as_markup()


def watch_keyboard(code: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🍿 СМОТРЕТЬ 🎬", callback_data=f"watch:{code}"))
    return builder.as_markup()
