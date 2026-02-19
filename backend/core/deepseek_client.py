"""DeepSeek API client for chat completions.

This module handles all communication with DeepSeek API,
including retry logic, error handling, and response parsing.
"""

import os
from typing import List, Dict, Any, Optional
import openai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from loguru import logger

from ..storage.models import Message


class DeepSeekClient:
    """Client for DeepSeek API with retry logic and error handling."""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com/v1"):
        """Initialize DeepSeek client.

        Args:
            api_key: DeepSeek API key
            base_url: API base URL (default: DeepSeek official)
        """
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = "deepseek-chat"  # можно позже сделать настраиваемым
        logger.info("DeepSeek client initialized")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((openai.APITimeoutError, openai.APIConnectionError)),
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying DeepSeek API call (attempt {retry_state.attempt_number})"
        )
    )
    async def chat_completion(
            self,
            messages: List[Dict[str, str]],
            temperature: float = 0.7,
            system_prompt: Optional[str] = None
    ) -> str:
        """Send chat completion request to DeepSeek API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Creativity (0.0-1.0)
            system_prompt: Optional system prompt to override default

        Returns:
            Assistant's response text

        Raises:
            openai.APIError: If API returns an error
            Exception: For unexpected errors
        """
        try:
            # Подготавливаем сообщения
            api_messages = []

            # Добавляем system prompt если есть
            if system_prompt:
                api_messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            # Добавляем историю чата
            api_messages.extend(messages)

            logger.debug(f"Sending request to DeepSeek with {len(messages)} messages")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                temperature=temperature
            )

            return response.choices[0].message.content

        except openai.APIError as e:
            logger.error(f"DeepSeek API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in DeepSeek call: {e}")
            raise

    def convert_to_api_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """Convert internal Message models to API format.

        Args:
            messages: List of Message objects

        Returns:
            List of dicts with 'role' and 'content'
        """
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    async def health_check(self) -> bool:
        """Check if DeepSeek API is accessible."""
        try:
            # Асинхронный вызов
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": "test"}],
                temperature=0.1,
                max_tokens=5  # ограничиваем, чтобы быстрее
            )
            # response уже не корутина, а объект
            return bool(response and response.choices)
        except Exception as e:
            logger.error(f"DeepSeek health check failed: {e}")
            return False