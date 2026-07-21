from app.database.models import TaskStatus, Priority


TASK_STATUS_EMOJI = {
    TaskStatus.CREATED: "📌",
    TaskStatus.IN_PROGRESS: "🚗",
    TaskStatus.COMPLETED: "✅",
    TaskStatus.FAILED: "❌",
    TaskStatus.CANCELLED: "🚫",
}

TASK_STATUS_LABEL = {
    TaskStatus.CREATED: "Создана",
    TaskStatus.IN_PROGRESS: "В процессе",
    TaskStatus.COMPLETED: "Завершена",
    TaskStatus.FAILED: "Провалена",
    TaskStatus.CANCELLED: "Отменена",
}

PRIORITY_EMOJI = {
    Priority.LOW: "🟢",
    Priority.MEDIUM: "🟡",
    Priority.HIGH: "🟠",
    Priority.URGENT: "🔴",
}

PRIORITY_LABEL = {
    Priority.LOW: "Низкий",
    Priority.MEDIUM: "Средний",
    Priority.HIGH: "Высокий",
    Priority.URGENT: "Срочно",
}