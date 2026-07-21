from datetime import datetime
from app.database.models import Task, TaskStatus, Priority
from app.utils.constants import TASK_STATUS_EMOJI, TASK_STATUS_LABEL, PRIORITY_EMOJI, PRIORITY_LABEL


def format_task_card(task: Task) -> str:
    status_emoji = TASK_STATUS_EMOJI.get(task.status, "📌")
    status_label = TASK_STATUS_LABEL.get(task.status, "Неизвестно")
    priority_emoji = PRIORITY_EMOJI.get(task.priority, "⚪")
    priority_label = PRIORITY_LABEL.get(task.priority, "Неизвестно")

    author_name = task.author.first_name if task.author else "Неизвестно"
    author_link = f'<a href="tg://user?id={task.author_id}">{author_name}</a>'

    assignee_text = "Не назначен"
    if task.assignee:
        assignee_text = f'<a href="tg://user?id={task.assignee_id}">{task.assignee.first_name}</a>'
    elif task.assignee_username:
        assignee_text = f"@{task.assignee_username} (ожидает регистрации)"

    lines = [
        f"📌 <b>ЗАДАЧА #{task.id}</b>",
        f"<b>От:</b> {author_link}",
        f"<b>Исполнитель:</b> {assignee_text}",
        f"<b>Статус:</b> {status_emoji} {status_label}",
        f"<b>Приоритет:</b> {priority_emoji} {priority_label}",
    ]

    if task.description:
        lines.append("")
        lines.append(f"<b>Описание:</b> {task.description}")

    if task.items:
        lines.append("")
        lines.append("<b>Список:</b>")
        for item in task.items:
            if item.is_completed:
                lines.append(f"[x] <s>{item.text}</s>")
            elif item.is_failed:
                lines.append(f"[✗] <s>{item.text}</s> (провалено)")
            else:
                lines.append(f"[ ] {item.text}")

    if task.updated_at:
        updated_str = task.updated_at.strftime("%Y-%m-%d %H:%M")
        lines.append("")
        lines.append(f"<i>Обновлено: {updated_str}</i>")

    return "\n".join(lines)


def format_task_list(tasks: list[Task], title: str = "Список задач") -> str:
    """Compact list of tasks for /my_current_tasks and /my_task_status."""
    if not tasks:
        return f"<b>{title}</b>\n\nНет активных задач."

    lines = [f"<b>{title}</b>\n"]
    for task in tasks:
        status_emoji = TASK_STATUS_EMOJI.get(task.status, "📌")
        status_label = TASK_STATUS_LABEL.get(task.status, "Неизвестно")
        priority_emoji = PRIORITY_EMOJI.get(task.priority, "⚪")

        assignee_text = "Не назначен"
        if task.assignee:
            assignee_text = task.assignee.first_name
        elif task.assignee_username:
            assignee_text = f"@{task.assignee_username}"

        lines.append(
            f"#{task.id} {status_emoji} {task.title[:50]}"
            f"{'…' if len(task.title) > 50 else ''}"
        )
        lines.append(
            f"   Статус: {status_label}  {priority_emoji}"
            f"  Исполнитель: {assignee_text}"
        )
        lines.append("")

    return "\n".join(lines)
