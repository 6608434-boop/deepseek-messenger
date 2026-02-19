"""Database operations for chat storage.

This module handles all database interactions:
- Creating tables
- Saving messages
- Retrieving chat history
- Managing chats
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import aiosqlite
from loguru import logger

from .models import Message, Chat


class Database:
    """Async SQLite database manager for chat storage."""

    def __init__(self, db_path: str = "chat.db"):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        logger.info(f"Database initialized at {db_path}")

    async def init_db(self):
        """Create tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица чатов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
            """)

            # Таблица сообщений
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE
                )
            """)

            # Индексы для быстрого поиска
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_chats_updated ON chats(updated_at)"
            )

            await db.commit()
            logger.info("Database tables initialized")

    async def create_chat(self, user_id: Optional[str] = None, title: str = "Новый чат") -> int:
        """Create a new chat.

        Args:
            user_id: Optional user identifier
            title: Chat title

        Returns:
            ID of created chat
        """
        now = datetime.now()

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO chats (user_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, title, now, now)
            )
            await db.commit()
            chat_id = cursor.lastrowid
            logger.info(f"Created new chat with ID {chat_id}")
            return chat_id

    async def save_message(self, chat_id: int, role: str, content: str) -> int:
        """Save a message to database.

        Args:
            chat_id: ID of the chat
            role: 'user' or 'assistant'
            content: Message content

        Returns:
            ID of saved message
        """
        now = datetime.now()

        async with aiosqlite.connect(self.db_path) as db:
            # Сохраняем сообщение
            cursor = await db.execute(
                """
                INSERT INTO messages (chat_id, role, content, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (chat_id, role, content, now)
            )

            # Обновляем время последнего сообщения в чате
            await db.execute(
                """
                UPDATE chats SET updated_at = ? WHERE id = ?
                """,
                (now, chat_id)
            )

            await db.commit()
            message_id = cursor.lastrowid
            logger.debug(f"Saved message {message_id} to chat {chat_id}")
            return message_id

    async def get_chat(self, chat_id: int) -> Optional[Chat]:
        """Get chat with all messages.

        Args:
            chat_id: ID of the chat

        Returns:
            Chat object with messages or None if not found
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Получаем информацию о чате
            cursor = await db.execute(
                """
                SELECT id, user_id, title, created_at, updated_at
                FROM chats WHERE id = ?
                """,
                (chat_id,)
            )
            chat_row = await cursor.fetchone()

            if not chat_row:
                return None

            # Получаем сообщения чата
            cursor = await db.execute(
                """
                SELECT id, chat_id, role, content, timestamp
                FROM messages WHERE chat_id = ?
                ORDER BY timestamp ASC
                """,
                (chat_id,)
            )
            message_rows = await cursor.fetchall()

            # Преобразуем в модели Pydantic
            messages = [
                Message(
                    id=row['id'],
                    chat_id=row['chat_id'],
                    role=row['role'],
                    content=row['content'],
                    timestamp=datetime.fromisoformat(row['timestamp'])
                )
                for row in message_rows
            ]

            chat = Chat(
                id=chat_row['id'],
                user_id=chat_row['user_id'],
                title=chat_row['title'],
                created_at=datetime.fromisoformat(chat_row['created_at']),
                updated_at=datetime.fromisoformat(chat_row['updated_at']),
                messages=messages
            )

            return chat

    async def get_chats_list(
            self,
            limit: int = 50,
            offset: int = 0,
            user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get list of chats (without messages).

        Args:
            limit: Maximum number of chats
            offset: Pagination offset
            user_id: Optional filter by user

        Returns:
            List of chat summaries
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            query = """
                SELECT 
                    c.id, c.user_id, c.title, c.created_at, c.updated_at,
                    COUNT(m.id) as message_count
                FROM chats c
                LEFT JOIN messages m ON c.id = m.chat_id
            """
            params = []

            if user_id:
                query += " WHERE c.user_id = ?"
                params.append(user_id)

            query += " GROUP BY c.id ORDER BY c.updated_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()

            return [
                {
                    "id": row['id'],
                    "user_id": row['user_id'],
                    "title": row['title'],
                    "created_at": row['created_at'],
                    "updated_at": row['updated_at'],
                    "message_count": row['message_count']
                }
                for row in rows
            ]

    async def delete_chat(self, chat_id: int) -> bool:
        """Delete chat and all its messages.

        Args:
            chat_id: ID of the chat to delete

        Returns:
            True if deleted, False if not found
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM chats WHERE id = ?",
                (chat_id,)
            )
            await db.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Deleted chat {chat_id}")
            return deleted

    async def get_last_n_messages(self, chat_id: int, n: int = 10) -> List[Message]:
        """Get last N messages from a chat.

        Args:
            chat_id: ID of the chat
            n: Number of messages to retrieve

        Returns:
            List of messages (most recent first)
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute(
                """
                SELECT id, chat_id, role, content, timestamp
                FROM messages
                WHERE chat_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (chat_id, n)
            )
            rows = await cursor.fetchall()

            # Возвращаем в хронологическом порядке (от старых к новым)
            messages = [
                Message(
                    id=row['id'],
                    chat_id=row['chat_id'],
                    role=row['role'],
                    content=row['content'],
                    timestamp=datetime.fromisoformat(row['timestamp'])
                )
                for row in reversed(rows)
            ]

            return messages