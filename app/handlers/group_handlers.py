from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_service import get_or_create_user

router = Router()


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def handle_group_message(message: Message, session: AsyncSession):
    """Automatically register group members when they send a message."""
    user = message.from_user
    if user:
        await get_or_create_user(session, user.id, user.username, user.first_name)