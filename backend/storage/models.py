"""Pydantic models for data validation and serialization.

This module defines all data structures used in the application:
- Message: individual chat messages
- Chat: conversation between user and AI
- API request/response models
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class Message(BaseModel):
    """Single message in a chat conversation."""

    id: Optional[int] = Field(None, description="Message ID in database")
    chat_id: Optional[int] = Field(None, description="ID of the chat this message belongs to")
    role: str = Field(..., description="'user' or 'assistant'", pattern="^(user|assistant)$")
    content: str = Field(..., description="Message text content", min_length=1)
    timestamp: datetime = Field(default_factory=datetime.now, description="When message was created")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "user",
                "content": "Привет! Как дела?",
                "timestamp": "2026-02-19T12:00:00"
            }
        }
    )


class Chat(BaseModel):
    """Chat conversation between user and AI."""

    id: Optional[int] = Field(None, description="Chat ID in database")
    user_id: Optional[str] = Field(None, description="User identifier (optional for now)")
    title: str = Field("Новый чат", description="Chat title")
    created_at: datetime = Field(default_factory=datetime.now, description="When chat was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last message timestamp")
    messages: List[Message] = Field(default_factory=list, description="Messages in this chat")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "DeepSeek тест",
                "messages": [
                    {
                        "role": "user",
                        "content": "Привет!"
                    }
                ]
            }
        }
    )


class ChatCreate(BaseModel):
    """Model for creating a new chat."""

    user_id: Optional[str] = None
    title: Optional[str] = "Новый чат"
    first_message: Optional[str] = None


class ChatUpdate(BaseModel):
    """Model for updating chat metadata."""

    title: Optional[str] = None


# API Request/Response Models

class ChatRequest(BaseModel):
    """Request model for /api/chat endpoint."""

    message: str = Field(..., description="User message", min_length=1, max_length=10000)
    chat_id: Optional[int] = Field(None, description="Existing chat ID or None for new chat")
    temperature: float = Field(0.7, description="Creativity (0.0-1.0)", ge=0.0, le=1.0)
    system_prompt: Optional[str] = Field(
        None,
        description="Optional system prompt to override default"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Расскажи про FastAPI",
                "chat_id": 1,
                "temperature": 0.8
            }
        }
    )


class ChatResponse(BaseModel):
    """Response model for /api/chat endpoint."""

    chat_id: int = Field(..., description="Chat ID")
    message: Message = Field(..., description="AI response message")
    success: bool = Field(True, description="Operation success status")
    error: Optional[str] = Field(None, description="Error message if any")


class ChatHistoryResponse(BaseModel):
    """Response model for /api/history endpoint."""

    chat: Chat = Field(..., description="Chat with all messages")
    success: bool = Field(True, description="Operation success status")
    error: Optional[str] = None


class ChatListResponse(BaseModel):
    """Response model for /api/chats endpoint."""

    chats: List[Dict[str, Any]] = Field(..., description="List of chats (without messages)")
    total: int = Field(..., description="Total number of chats")
    success: bool = Field(True, description="Operation success status")


class HealthResponse(BaseModel):
    """Response model for /api/health endpoint."""

    status: str = Field("ok", description="Service status")
    version: str = Field("1.0.0", description="API version")
    timestamp: datetime = Field(default_factory=datetime.now)
    deepseek_api: str = Field("unknown", description="DeepSeek API status")
    database: str = Field("unknown", description="Database status")