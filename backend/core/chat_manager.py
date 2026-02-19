"""Chat management and orchestration logic.

This module handles:
- Processing user messages
- Managing chat history
- Coordinating between database and DeepSeek API
"""

from typing import List, Optional, Dict, Any
from loguru import logger

from ..storage.models import Message, Chat, ChatRequest
from ..storage.db import Database
from .deepseek_client import DeepSeekClient


class ChatManager:
    """Orchestrates chat operations between database and AI."""

    def __init__(self, db: Database, deepseek_client: DeepSeekClient):
        """Initialize chat manager.

        Args:
            db: Database instance
            deepseek_client: DeepSeek API client
        """
        self.db = db
        self.deepseek = deepseek_client
        logger.info("Chat manager initialized")

    async def process_message(
            self,
            message: str,
            chat_id: Optional[int] = None,
            temperature: float = 0.7,
            system_prompt: Optional[str] = None,
            user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process user message and get AI response.

        This is the main entry point for chat interactions.

        Args:
            message: User message text
            chat_id: Existing chat ID or None for new chat
            temperature: Creativity (0.0-1.0)
            system_prompt: Optional system prompt override
            user_id: Optional user identifier

        Returns:
            Dict with chat_id and AI response message
        """
        try:
            # 1. Создаём новый чат если нужно
            if chat_id is None:
                chat_id = await self.db.create_chat(
                    user_id=user_id,
                    title=message[:50] + "..." if len(message) > 50 else message
                )
                logger.info(f"Created new chat {chat_id} for message")

            # 2. Сохраняем сообщение пользователя
            user_message_id = await self.db.save_message(
                chat_id=chat_id,
                role="user",
                content=message
            )
            logger.debug(f"Saved user message {user_message_id}")

            # 3. Получаем последние N сообщений для контекста
            last_messages = await self.db.get_last_n_messages(chat_id, n=10)

            # 4. Конвертируем в формат API
            api_messages = self.deepseek.convert_to_api_messages(last_messages)

            # 5. Отправляем в DeepSeek
            ai_response = await self.deepseek.chat_completion(
                messages=api_messages,
                temperature=temperature,
                system_prompt=system_prompt
            )

            # 6. Сохраняем ответ ассистента
            assistant_message_id = await self.db.save_message(
                chat_id=chat_id,
                role="assistant",
                content=ai_response
            )
            logger.debug(f"Saved assistant message {assistant_message_id}")

            # 7. Возвращаем результат
            return {
                "chat_id": chat_id,
                "message": Message(
                    id=assistant_message_id,
                    chat_id=chat_id,
                    role="assistant",
                    content=ai_response,
                    timestamp=datetime.now()
                ),
                "success": True
            }

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "chat_id": chat_id,
                "message": None,
                "success": False,
                "error": str(e)
            }

    async def get_chat_history(self, chat_id: int) -> Optional[Chat]:
        """Get full chat history.

        Args:
            chat_id: ID of the chat

        Returns:
            Chat object with messages or None
        """
        try:
            chat = await self.db.get_chat(chat_id)
            return chat
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return None

    async def get_chats_list(
            self,
            limit: int = 50,
            offset: int = 0,
            user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get list of chats without messages.

        Args:
            limit: Maximum number of chats
            offset: Pagination offset
            user_id: Optional filter by user

        Returns:
            List of chat summaries
        """
        try:
            chats = await self.db.get_chats_list(
                limit=limit,
                offset=offset,
                user_id=user_id
            )
            return chats
        except Exception as e:
            logger.error(f"Error getting chats list: {e}")
            return []

    async def delete_chat(self, chat_id: int) -> bool:
        """Delete a chat and all its messages.

        Args:
            chat_id: ID of the chat to delete

        Returns:
            True if deleted, False otherwise
        """
        try:
            return await self.db.delete_chat(chat_id)
        except Exception as e:
            logger.error(f"Error deleting chat: {e}")
            return False

    async def health_check(self) -> Dict[str, str]:
        """Check health of all dependencies.

        Returns:
            Dict with status of each component
        """
        status = {
            "database": "unknown",
            "deepseek_api": "unknown"
        }

        # Проверяем базу данных
        try:
            # Пробуем создать временную таблицу
            await self.db.init_db()
            status["database"] = "ok"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            status["database"] = "error"

        # Проверяем DeepSeek API
        try:
            api_status = await self.deepseek.health_check()
            status["deepseek_api"] = "ok" if api_status else "error"
        except Exception as e:
            logger.error(f"DeepSeek health check failed: {e}")
            status["deepseek_api"] = "error"

        return status


# Import at the bottom to avoid circular imports
from datetime import datetime