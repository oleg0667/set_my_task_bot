import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean,
    DateTime, Enum, ForeignKey, func
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class TaskStatus(str, enum.Enum):
    CREATED = "CREATED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Priority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tasks_created = relationship("Task", back_populates="author", foreign_keys="Task.author_id")
    tasks_assigned = relationship("Task", back_populates="assignee", foreign_keys="Task.assignee_id")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    author_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    assignee_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    assignee_username = Column(String, nullable=True)
    chat_id = Column(BigInteger, nullable=False)
    message_id = Column(BigInteger, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.CREATED, nullable=False)
    priority = Column(Enum(Priority), default=Priority.MEDIUM, nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    author = relationship("User", back_populates="tasks_created", foreign_keys=[author_id])
    assignee = relationship("User", back_populates="tasks_assigned", foreign_keys=[assignee_id])
    items = relationship("TaskItem", back_populates="task", cascade="all, delete-orphan")


class TaskItem(Base):
    __tablename__ = "task_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    text = Column(String, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    is_failed = Column(Boolean, default=False, nullable=False)

    task = relationship("Task", back_populates="items")
