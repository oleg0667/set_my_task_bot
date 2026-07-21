from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database.models import Task, TaskStatus, TaskItem


class TaskCallback(CallbackData, prefix="task"):
    action: str  # next_status, fail, cancel, complete_item, fail_item, noop
    task_id: int
    item_id: int | None = None


def build_task_keyboard(task: Task, user_id: int) -> InlineKeyboardBuilder:
    from aiogram.utils.keyboard import InlineKeyboardButton

    builder = InlineKeyboardBuilder()

    is_author = task.author_id == user_id
    is_assignee = task.assignee_id == user_id
    can_act = is_assignee or (task.assignee_id is None and is_author)

    if task.status in (TaskStatus.CREATED, TaskStatus.IN_PROGRESS):
        # Progress row: single button or two buttons
        if can_act and task.status == TaskStatus.CREATED:
            builder.row(
                InlineKeyboardButton(
                    text="🚀 Принять в работу",
                    callback_data=TaskCallback(action="next_status", task_id=task.id).pack(),
                )
            )
        elif can_act and task.status == TaskStatus.IN_PROGRESS:
            builder.row(
                InlineKeyboardButton(
                    text="✅ Завершить",
                    callback_data=TaskCallback(action="next_status", task_id=task.id).pack(),
                ),
                InlineKeyboardButton(
                    text="❌ Провалено",
                    callback_data=TaskCallback(action="fail", task_id=task.id).pack(),
                ),
            )

        # Checklist items — each unresolved item gets ✅ / ❌ buttons
        if can_act:
            for item in task.items:
                if item.is_completed:
                    builder.row(
                        InlineKeyboardButton(
                            text=f"☑️ {item.text[:35]}",
                            callback_data=TaskCallback(action="noop", task_id=task.id).pack(),
                        )
                    )
                elif item.is_failed:
                    builder.row(
                        InlineKeyboardButton(
                            text=f"❌ {item.text[:35]}",
                            callback_data=TaskCallback(action="noop", task_id=task.id).pack(),
                        )
                    )
                else:
                    # Two buttons side by side: ✅ and ❌
                    builder.row(
                        InlineKeyboardButton(
                            text=f"✅ {item.text[:20]}",
                            callback_data=TaskCallback(
                                action="complete_item", task_id=task.id, item_id=item.id
                            ).pack(),
                        ),
                        InlineKeyboardButton(
                            text=f"❌ {item.text[:20]}",
                            callback_data=TaskCallback(
                                action="fail_item", task_id=task.id, item_id=item.id
                            ).pack(),
                        ),
                    )

        # Cancel button (only author)
        if is_author:
            builder.row(
                InlineKeyboardButton(
                    text="🚫 Отменить",
                    callback_data=TaskCallback(action="cancel", task_id=task.id).pack(),
                )
            )

    return builder
