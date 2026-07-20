from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database.models import Task, TaskStatus, TaskItem


class TaskCallback(CallbackData, prefix="task"):
    action: str  # take, complete, cancel, toggle_item
    task_id: int
    item_id: int | None = None


def build_task_keyboard(task: Task, user_id: int) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()

    is_author = task.author_id == user_id
    is_assignee = task.assignee_id == user_id

    # Only show action buttons for CREATED or IN_PROGRESS status
    if task.status in (TaskStatus.CREATED, TaskStatus.IN_PROGRESS):
        # "Take Task" button — for unassigned tasks or if assignee clicks
        if task.assignee_id is None or (
            task.assignee_id == user_id and task.status == TaskStatus.CREATED
        ):
            builder.button(
                text="🚀 Взять в работу",
                callback_data=TaskCallback(action="take", task_id=task.id),
            )

        # Checklist item buttons
        for item in task.items:
            item_text = f"{'☑️' if item.is_completed else '⬜️'} {item.text}"
            builder.button(
                text=item_text,
                callback_data=TaskCallback(
                    action="toggle_item", task_id=task.id, item_id=item.id
                ),
            )

        # Complete button (only assignee or author if no assignee)
        if is_assignee or (task.assignee_id is None and is_author):
            builder.button(
                text="✅ Завершить",
                callback_data=TaskCallback(action="complete", task_id=task.id),
            )

        # Cancel button (only author)
        if is_author:
            builder.button(
                text="❌ Отменить",
                callback_data=TaskCallback(action="cancel", task_id=task.id),
            )

    builder.adjust(1)

    return builder