# Technical Specification (PRD / Specs)
## Telegram Task Management Bot ("FamilyTaskBot")

### 1. Overview
This specification document guides the AI coding agent (**Cline**) in building an asynchronous Telegram bot for personal and family task delegation. The bot enables users to assign tasks to contacts (whether they are in a shared group chat or in private messages), track task progress in real time via interactive inline keyboards, manage checklist items, and handle state transitions efficiently without message spam.

---

### 2. Tech Stack & Environment Requirements

#### 2.1 Virtual Environment & Python Setup
* **Python Version:** `Python 3.11+`
* **Virtual Environment Tool:** `venv` (standard library) or `uv`
* **Setup Commands:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
  ```

#### 2.2 Key Dependencies (`requirements.txt`)
* `aiogram>=3.4.0` — Asynchronous Telegram Bot API framework.
* `pydantic-settings>=2.0.0` — Type-safe environment configuration management.
* `sqlalchemy[asyncio]>=2.0.0` — Async ORM for database operations.
* `aiosqlite>=0.19.0` — Async driver for SQLite (lightweight local storage).
* `alembic>=1.13.0` — Database schema migrations.
* `python-dotenv>=1.0.0` — `.env` configuration file loader.

---

### 3. Project Directory Structure

```text
telegram-task-bot/
├── .env.example
├── .gitignore
├── README.md
├── specs.md
├── requirements.txt
├── alembic.ini
├── app/
│   ├── __init__.py
│   ├── main.py                 # Bot entrypoint & dispatcher initialization
│   ├── config.py               # Pydantic Settings configuration
│   ├── database/
│   │   ├── __init__.py
│   │   ├── session.py          # Async engine and session maker
│   │   └── models.py           # SQLAlchemy ORM models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── task_service.py     # Business logic for task CRUD & state transitions
│   │   └── user_service.py     # User registration and lookup
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py            # /start command & deeplink handling
│   │   ├── tasks.py            # Task creation (/task) & direct commands
│   │   ├── inline_callbacks.py # Button click callbacks (Status, Checklists)
│   │   └── group_handlers.py  # Group-specific events & commands
│   ├── keyboards/
│   │   ├── __init__.py
│   │   ├── inline_task.py      # Task card inline keyboard builders
│   │   └── reply_menu.py       # Main menu keyboards (if applicable)
│   └── utils/
│       ├── __init__.py
│       ├── formatters.py       # Telegram HTML text formatters for tasks
│       └── constants.py        # Enums for Task Status, Roles, etc.
```

---

### 4. Database Schema Design

#### 4.1 Enums
* **`TaskStatus`**: `CREATED` (pending), `IN_PROGRESS` (in work), `COMPLETED` (done), `CANCELLED` (revoked).
* **`Priority`**: `LOW`, `MEDIUM`, `HIGH`, `URGENT`.

#### 4.2 Tables (`app/database/models.py`)

##### `users` Table
* `id` (BigInteger, Primary Key): Telegram User ID (`user.id`).
* `username` (String, nullable): Telegram `@username`.
* `first_name` (String): User's first name.
* `created_at` (DateTime UTC): Registration timestamp.

##### `tasks` Table
* `id` (Integer, Primary Key, Auto-increment): Unique Task ID.
* `title` (String): Main task description/headline.
* `description` (Text, nullable): Extended notes or location links.
* `author_id` (BigInteger, Foreign Key -> `users.id`): Creator of the task.
* `assignee_id` (BigInteger, Foreign Key -> `users.id`, nullable): Assigned executor.
* `chat_id` (BigInteger): Telegram Chat ID where the main message card resides.
* `message_id` (BigInteger, nullable): Telegram Message ID for live UI updating.
* `status` (Enum `TaskStatus`): Current state (default `CREATED`).
* `priority` (Enum `Priority`): Priority level (default `MEDIUM`).
* `due_date` (DateTime, nullable): Optional deadline.
* `created_at` (DateTime UTC): Creation timestamp.
* `updated_at` (DateTime UTC): Last update timestamp.

##### `task_items` Table (Checklist Items)
* `id` (Integer, Primary Key, Auto-increment): Checklist item ID.
* `task_id` (Integer, Foreign Key -> `tasks.id`, On Delete CASCADE): Task reference.
* `text` (String): Item text (e.g. "Bread", "Milk").
* `is_completed` (Boolean): Default `False`.

---

### 5. Key Functional Modules & Logic

#### 5.1 Telegram API Constraints & Non-Group User Handling (Deeplinking)
* **Constraint:** Telegram prevents bots from initiating private conversations with users who have not interacted with the bot (`/start`).
* **Solution (Deeplink Flow):**
  1. Author creates a task assigned to `@username` who has never started the bot, or creates an unassigned task.
  2. Bot generates a unique invite link: `t.me/<bot_username>?start=task_<task_id>`.
  3. Author forwards this link or sends it directly to the intended executor.
  4. When the executor clicks the link, the bot handles `/start task_<task_id>`, registers the user, links them to the task, and opens the interactive task card in private chat.

#### 5.2 Task Lifecycle & State Transitions

```text
[ CREATED ] ───( Assignee clicks "In Progress" )───> [ IN_PROGRESS ]
     │                                                      │
     ├───( Author/Assignee clicks "Complete" )──────────────┼───> [ COMPLETED ]
     │                                                      │
     └───( Author clicks "Cancel" )─────────────────────────┴───> [ CANCELLED ]
```

#### 5.3 Task Message Card UI Format (HTML)
Task messages should be updated in-place via `bot.edit_message_text` to reduce chat clutter.

```html
📌 <b>ЗАДАЧА #104</b>
<b>От:</b> <a href="tg://user?id=123456">Олег</a>
<b>Исполнитель:</b> @wife_username (или "Не назначен")
<b>Статус:</b> 🚗 В процессе
<b>Приоритет:</b> 🔴 Срочно

<b>Описание:</b> Зайти в аптеку по пути домой.

<b>Список:</b>
[x] <s>Нурофен 400мг</s>
[ ] Пластырь бактерицидный
[ ] Аспирин

<i>Обновлено: 2026-07-20 12:00</i>
```

#### 5.4 Inline Keyboards Layout

##### State: `CREATED` / `IN_PROGRESS`
* **Row 1:** `[ 🚀 Взять в работу ]` (if unassigned or assigned to clicker)
* **Row 2:** Dynamic checklist buttons `[ ☑️ Нурофен ]` `[ ⬜️ Пластырь ]` (toggles completed state)
* **Row 3:** `[ ✅ Завершить ]` `[ ❌ Отменить (Только Автор) ]`

---

### 6. Step-by-Step Implementation Instructions for Cline

Cline should execute the development process in the following sequential order:

#### Milestone 1: Virtual Environment & Boilerplate Setup
1. Create Python virtual environment: `python3 -m venv venv`.
2. Activate environment and generate `requirements.txt` with `aiogram`, `sqlalchemy`, `aiosqlite`, `pydantic-settings`, `python-dotenv`.
3. Create `.env.example` with `BOT_TOKEN`, `DB_URL=sqlite+aiosqlite:///./tasks.db`.
4. Build `app/config.py` using `pydantic-settings`.

#### Milestone 2: Database Layer & Models
1. Implement SQLAlchemy 2.0 async models in `app/database/models.py`.
2. Setup async session generator in `app/database/session.py`.
3. Write script/init logic to create database tables on bot startup.

#### Milestone 3: Task Service & Formatters
1. Create `app/services/task_service.py` to handle CRUD operations:
   * `create_task(...)`
   * `assign_task(...)`
   * `update_status(...)`
   * `toggle_item(...)`
2. Create `app/utils/formatters.py` for HTML card text generation.

#### Milestone 4: Keyboards & Callback Handling
1. Implement `app/keyboards/inline_task.py` using `CallbackData` classes for robust typing (e.g. `TaskCallback(action="take", task_id=104)`).
2. Build inline handlers in `app/handlers/inline_callbacks.py` with proper error messages (e.g. `answer_callback_query(..., alert=True)` if non-author tries to cancel).

#### Milestone 5: Commands & Deeplink Mechanics
1. Implement `/start` command in `app/handlers/start.py` handling parameters like `task_104`.
2. Implement `/task` command in `app/handlers/tasks.py` supporting text parsing for multi-line checklists (e.g., lines starting with `- ` or `* ` become checklist items).
3. Connect all routers in `app/main.py` and ensure graceful shutdown.

---

### 7. Security & Business Rules
1. **Access Control:**
   * Only the **Author** can cancel a task.
   * Only the **Assignee** (or Author if no assignee set) can mark items or finish the task.
   * Anyone in the group can click "Take Task" if it is currently unassigned.
2. **Notification Policy:**
   * Notification on status change is sent directly to the task author via private message or reply in chat.
   * Modifying checklist items edits the existing card silently without sending new messages.
