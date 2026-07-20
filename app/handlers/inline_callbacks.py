from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_session
from app.database.models import TaskStatus
from app.services.user_service import get_or_create_user
from app.services.task_service import (
    get_task_by_id,
    assign_task,
    update_task_status,
    toggle_task_item,
    update_task_message_id,
)
from app.utils.formatters import format_task_card
from app.keyboards.inline_task import TaskCallback, build_task_keyboard
from app.config import settings

router = Router()


@router.callback_query(TaskCallback.filter())
async def handle_task_callback(
    query: CallbackQuery,
    callback_data: TaskCallback,
    session: AsyncSession,
):
    user = query.from_user
    await get_or_create_user(session, user.id, user.username, user.first_name)

    task = await get_task_by_id(session, callback_data.task_id)
    if task is None:
        await query.answer("❌ Задача не найдена.", show_alert=True)
        return

    action = callback_data.action
    is_author = task.author_id == user.id
    is_assignee = task.assignee_id == user.id

    if action == "take":
        # Anyone can take an unassigned task
        if task.assignee_id is not None and not is_assignee:
            await query.answer("❌ Задача уже назначена другому исполнителю.", show_alert=True)
            return
        task = await assign_task(session, task.id, user.id)
        await query.answer("✅ Задача взята в работу!")

    elif action == "toggle_item":
        if callback_data.item_id is None:
            await query.answer("❌ Пункт не указан.", show_alert=True)
            return
        # Only assignee or author (if no assignee) can toggle items
        if not is_assignee and not (task.assignee_id is None and is_author):
            await query.answer("❌ Вы не можете изменять этот список.", show_alert=True)
            return
        item = await toggle_task_item(session, callback_data.item_id)
        if item is None:
            await query.answer("❌ Пункт не найден.", show_alert=True)
            return
        await query.answer("✅ Пункт обновлён.")

    elif action == "complete":
        # Only assignee or author (if no assignee) can complete
        if not is_assignee and not (task.assignee_id is None and is_author):
            await query.answer("❌ Вы не можете завершить эту задачу.", show_alert=True)
            return
        task = await update_task_status(session, task.id, TaskStatus.COMPLETED)
        await query.answer("✅ Задача завершена!")

    elif action == "cancel":
        # Only author can cancel
        if not is_author:
            await query.answer("❌ Только автор может отменить задачу.", show_alert=True)
            return
        task = await update_task_status(session, task.id, TaskStatus.CANCELLED)
        await query.answer("❌ Задача отменена.")

    else:
        await query.answer("❌ Неизвестное действие.", show_alert=True)
        return

    # Reload task and update the message
    task = await get_task_by_id(session, callback_data.task_id)
    if task and query.message:
        text = format_task_card(task)
        keyboard = build_task_keyboard(task, user.id)
        try:
            await query.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard.as_markup())
        except Exception:
            pass  # Message content might be the same