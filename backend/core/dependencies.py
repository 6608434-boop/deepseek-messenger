"""Dependency injection for FastAPI.

This module provides:
- Database instance
- DeepSeek client instance
- Chat manager instance
"""

import os
from functools import lru_cache
from dotenv import load_dotenv
from loguru import logger

from ..storage.db import Database
from .deepseek_client import DeepSeekClient
from .chat_manager import ChatManager

# Load environment variables
load_dotenv()


@lru_cache
def get_settings():
    """Get application settings from environment."""
    return {
        "deepseek_api_key": os.getenv("DEEPSEEK_API_KEY"),
        "deepseek_api_url": os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1"),
        "database_path": os.getenv("DATABASE_PATH", "./chat.db"),
    }


# Singleton instances
_db_instance: Database = None
_deepseek_instance: DeepSeekClient = None
_chat_manager_instance: ChatManager = None


async def get_db() -> Database:
    """Get or create database instance."""
    global _db_instance

    if _db_instance is None:
        settings = get_settings()
        _db_instance = Database(db_path=settings["database_path"])
        await _db_instance.init_db()
        logger.info("Database instance created")

    return _db_instance


async def get_deepseek_client() -> DeepSeekClient:
    """Get or create DeepSeek client instance."""
    global _deepseek_instance

    if _deepseek_instance is None:
        settings = get_settings()

        if not settings["deepseek_api_key"]:
            logger.error("DEEPSEEK_API_KEY not set in environment")
            raise ValueError("DEEPSEEK_API_KEY is required")

        _deepseek_instance = DeepSeekClient(
            api_key=settings["deepseek_api_key"],
            base_url=settings["deepseek_api_url"]
        )
        logger.info("DeepSeek client instance created")

    return _deepseek_instance


async def get_chat_manager() -> ChatManager:
    """Get or create chat manager instance."""
    global _chat_manager_instance

    if _chat_manager_instance is None:
        db = await get_db()
        deepseek = await get_deepseek_client()
        _chat_manager_instance = ChatManager(db=db, deepseek_client=deepseek)
        logger.info("Chat manager instance created")

    return _chat_manager_instance


async def close_connections():
    """Clean up connections (call on shutdown)."""
    global _db_instance, _deepseek_instance, _chat_manager_instance

    logger.info("Closing database connections...")
    # SQLite doesn't need explicit close for aiosqlite,
    # but we'll clear instances

    _db_instance = None
    _deepseek_instance = None
    _chat_manager_instance = None

    logger.info("All connections closed")