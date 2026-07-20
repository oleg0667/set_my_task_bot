import re
from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_session
from app.services.user_service import get_or_create_user
from app.services.task_service import get_task_by_id, assign_task, update_task_message_id
from app.utils.formatters import format_task_card
from app.keyboards.inline_task import build_task_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, session: AsyncSession):
    user = message.from_user
    await get_or_create_user(session, user.id, user.username, user.first_name)

    args = command.args
    if args and args.startswith("task_"):
        # Deeplink: /start task_<id>
        match = re.match(r"task_(\d+)", args)
        if match:
            task_id = int(match.group(1))
            task = await get_task_by_id(session, task_id)
            if task:
                # Assign the user to the task if it's unassigned
                if task.assignee_id is None:
                    task = await assign_task(session, task_id, user.id)
                # Update message_id in private chat
                text = format_task_card(task)
                keyboard = build_task_keyboard(task, user.id)
                sent = await message.answer(text, parse_mode="HTML", reply_markup=keyboard.as_markup())
                await update_task_message_id(session, task_id, sent.message_id)
                return

    await message.answer(
        "👋 Привет! Я FamilyTaskBot — бот для управления задачами.\n\n"
        "Используй команду /task чтобы создать новую задачу.\n"
        "Можно указать:\n"
        "• Текст задачи (первая строка — заголовок)\n"
        "• Список пунктов через /task или строки с - или *\n"
        "• Исполнителя через @username в тексте"
    )