import re
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_session
from app.database.models import Priority
from app.services.user_service import get_or_create_user, get_user_by_id, get_user_by_username
from app.services.task_service import create_task, get_task_by_id, update_task_message_id
from app.utils.formatters import format_task_card
from app.keyboards.inline_task import build_task_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("task"))
async def cmd_task(message: Message, session: AsyncSession):
    user = message.from_user
    await get_or_create_user(session, user.id, user.username, user.first_name)

    chat_id = message.chat.id
    text = message.text or ""
    logger.info(f"Received /task command from user {user.id} in chat {chat_id}: {text!r}")

    # Remove /task command prefix
    body = text.removeprefix("/task").strip()

    if not body:
        await message.answer(
            "❌ Укажите описание задачи.\n\n"
            "Пример:\n"
            "<code>/task Купить продукты в магазине\n"
            "- Хлеб\n"
            "- Молоко\n"
            "- Яйца</code>\n\n"
            "Можно указать @username исполнителя.",
            parse_mode="HTML",
        )
        return

    lines = body.split("\n")
    title = lines[0].strip()
    description_lines = []
    checklist_items = []
    assignee_username = None

    # Check for @mention in the title line itself
    title_mention_match = re.search(r"@(\w+)", title)
    if title_mention_match:
        assignee_username = title_mention_match.group(1)
        # Remove @mention from the title
        title = title.replace(f"@{assignee_username}", "").strip()
        logger.info(f"Found assignee @{assignee_username} in title, cleaned title: {title!r}")

    for line in lines[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        # Check for @mention
        mention_match = re.search(r"@(\w+)", stripped)
        if mention_match:
            assignee_username = mention_match.group(1)
            # Remove @mention from line
            cleaned = stripped.replace(f"@{assignee_username}", "").strip()
            if cleaned and (cleaned.startswith("- ") or cleaned.startswith("* ")):
                checklist_items.append(cleaned[2:].strip())
            elif cleaned and not cleaned.startswith("-") and not cleaned.startswith("*"):
                description_lines.append(cleaned)
        elif stripped.startswith("- ") or stripped.startswith("* "):
            checklist_items.append(stripped[2:].strip())
        else:
            description_lines.append(stripped)

    description = "\n".join(description_lines) if description_lines else None

    assignee_id = None
    if assignee_username:
        # Look up the user by username in the database
        assignee_user = await get_user_by_username(session, assignee_username)
        if assignee_user:
            assignee_id = assignee_user.id
            logger.info(f"Found assignee @{assignee_username} in DB (id={assignee_id})")
        else:
            logger.info(f"Assignee @{assignee_username} not found in DB — will be assigned via deeplink later")

    # Parse priority from title (e.g. !high, !urgent, !low)
    priority_map = {
        "!low": Priority.LOW,
        "!medium": Priority.MEDIUM,
        "!high": Priority.HIGH,
        "!urgent": Priority.URGENT,
    }
    task_priority = Priority.MEDIUM
    for keyword, priority in priority_map.items():
        if keyword in title.lower():
            task_priority = priority
            # Remove the priority keyword from the title
            title = re.sub(re.escape(keyword), "", title, flags=re.IGNORECASE).strip()
            break

    logger.info(f"Creating task: title={title!r}, author_id={user.id}, chat_id={chat_id}, assignee_username={assignee_username}, priority={task_priority.value}")

    task = await create_task(
        session=session,
        title=title,
        author_id=user.id,
        chat_id=chat_id,
        description=description,
        assignee_id=assignee_id,
        assignee_username=assignee_username if not assignee_id else None,
        priority=task_priority,
        items_text=checklist_items if checklist_items else None,
    )

    text_card = format_task_card(task)
    keyboard = build_task_keyboard(task, user.id)
    sent = await message.answer(text_card, parse_mode="HTML", reply_markup=keyboard.as_markup())
    await update_task_message_id(session, task.id, sent.message_id)

    # If assignee was not found in DB, show a deeplink to invite them
    if assignee_username and not assignee_id:
        bot_username = (await message.bot.me()).username
        deep_link = f"https://t.me/{bot_username}?start=task_{task.id}"
        await message.answer(
            f"🔗 Исполнитель @{assignee_username} не зарегистрирован в боте.\n"
            f"Отправьте ему эту ссылку для назначения задачи:\n"
            f"<code>{deep_link}</code>",
            parse_mode="HTML",
        )

    logger.info(f"Task #{task.id} created successfully, message_id={sent.message_id}")
