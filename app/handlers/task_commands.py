import re
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.task_service import (
    get_task_by_id,
    get_tasks_by_assignee,
    get_tasks_by_chat,
)
from app.utils.formatters import format_task_card, format_task_list

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("my_task_status"))
async def cmd_my_task_status(message: Message, session: AsyncSession):
    """Show status of a task by ID (for the author to check progress)."""
    user = message.from_user
    text = message.text or ""

    # Parse task ID from command arguments or from reply
    parts = text.strip().split(maxsplit=1)
    task_id = None

    if len(parts) > 1:
        try:
            task_id = int(parts[1].strip())
        except ValueError:
            pass
    elif message.reply_to_message:
        # Try to find task ID in the replied message
        reply_text = message.reply_to_message.text or ""
        match = re.search(r"#(\d+)", reply_text)
        if match:
            task_id = int(match.group(1))

    if task_id is None:
        await message.answer(
            "📋 Укажите ID задачи.\n\n"
            "Пример:\n"
            "<code>/my_task_status 5</code>\n\n"
            "Или ответьте на сообщение с карточкой задачи этой командой.",
            parse_mode="HTML",
        )
        return

    task = await get_task_by_id(session, task_id)
    if task is None:
        await message.answer(f"❌ Задача #{task_id} не найдена.")
        return

    # Only author or assignee can view
    if task.author_id != user.id and task.assignee_id != user.id:
        await message.answer("❌ Вы не автор и не исполнитель этой задачи.")
        return

    text_card = format_task_card(task)
    await message.answer(text_card, parse_mode="HTML")


@router.message(Command("my_current_tasks"))
async def cmd_my_current_tasks(message: Message, session: AsyncSession):
    """Show all active tasks assigned to the current user."""
    user = message.from_user

    tasks = await get_tasks_by_assignee(session, user.id)
    text = format_task_list(tasks, title="📋 Мои текущие задачи")
    await message.answer(text, parse_mode="HTML")


@router.message(Command("current_task"))
async def cmd_current_task(message: Message, session: AsyncSession):
    """Show all active tasks in the current chat/group."""
    chat_id = message.chat.id
    user = message.from_user

    tasks = await get_tasks_by_chat(session, chat_id)
    text = format_task_list(tasks, title=f"📋 Задачи в этом чате")
    await message.answer(text, parse_mode="HTML")