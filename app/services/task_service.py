from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Task, TaskItem, TaskStatus, Priority


async def create_task(
    session: AsyncSession,
    title: str,
    author_id: int,
    chat_id: int,
    description: str | None = None,
    assignee_id: int | None = None,
    assignee_username: str | None = None,
    priority: Priority = Priority.MEDIUM,
    items_text: list[str] | None = None,
) -> Task:
    task = Task(
        title=title,
        description=description,
        author_id=author_id,
        assignee_id=assignee_id,
        assignee_username=assignee_username,
        chat_id=chat_id,
        status=TaskStatus.CREATED,
        priority=priority,
    )
    session.add(task)
    await session.flush()

    if items_text:
        for text in items_text:
            item = TaskItem(task_id=task.id, text=text)
            session.add(item)

    await session.commit()
    await session.refresh(task)
    # Eagerly load relationships
    result = await session.execute(
        select(Task)
        .options(joinedload(Task.author), joinedload(Task.assignee), joinedload(Task.items))
        .where(Task.id == task.id)
    )
    return result.unique().scalar_one()


async def get_task_by_id(session: AsyncSession, task_id: int) -> Task | None:
    result = await session.execute(
        select(Task)
        .options(joinedload(Task.author), joinedload(Task.assignee), joinedload(Task.items))
        .where(Task.id == task_id)
    )
    return result.unique().scalar_one_or_none()


async def assign_task(session: AsyncSession, task_id: int, assignee_id: int) -> Task | None:
    task = await get_task_by_id(session, task_id)
    if task is None:
        return None
    task.assignee_id = assignee_id
    await session.commit()
    return await get_task_by_id(session, task_id)


async def update_task_status(session: AsyncSession, task_id: int, new_status: TaskStatus) -> Task | None:
    task = await get_task_by_id(session, task_id)
    if task is None:
        return None
    task.status = new_status
    await session.commit()
    return await get_task_by_id(session, task_id)


async def toggle_task_item(session: AsyncSession, item_id: int) -> TaskItem | None:
    result = await session.execute(select(TaskItem).where(TaskItem.id == item_id))
    item = result.scalar_one_or_none()
    if item is None:
        return None
    item.is_completed = not item.is_completed
    await session.commit()
    await session.refresh(item)
    return item


async def get_pending_tasks_by_username(session: AsyncSession, username: str) -> list[Task]:
    """Find tasks that are unassigned and have matching assignee_username."""
    result = await session.execute(
        select(Task)
        .options(joinedload(Task.author), joinedload(Task.assignee), joinedload(Task.items))
        .where(
            Task.assignee_id.is_(None),
            Task.assignee_username == username,
            Task.status.in_([TaskStatus.CREATED, TaskStatus.IN_PROGRESS]),
        )
    )
    return list(result.unique().scalars().all())


async def update_task_message_id(session: AsyncSession, task_id: int, message_id: int) -> None:
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task:
        task.message_id = message_id
        await session.commit()
