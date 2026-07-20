import logging
from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_service import get_or_create_user
from app.services.task_service import get_pending_tasks_by_username, assign_task

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def handle_group_message(message: Message, session: AsyncSession):
    """Automatically register group members when they send a message."""
    user = message.from_user
    if user:
        await get_or_create_user(session, user.id, user.username, user.first_name)
        # Check if there are pending tasks waiting for this user by username
        if user.username:
            pending = await get_pending_tasks_by_username(session, user.username)
            for pending_task in pending:
                if pending_task.assignee_id is None:
                    await assign_task(session, pending_task.id, user.id)
                    logger.info(f"Auto-assigned task #{pending_task.id} to @{user.username} (id={user.id})")
