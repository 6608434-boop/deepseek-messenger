"""API routes for the chat application.

This module defines all REST endpoints:
- POST /api/chat - Send message
- GET /api/history/{chat_id} - Get chat history
- GET /api/chats - List all chats
- DELETE /api/chat/{chat_id} - Delete chat
- GET /api/health - Health check
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger

from ..storage.models import (
    ChatRequest, ChatResponse, ChatHistoryResponse,
    ChatListResponse, HealthResponse
)
from ..core.chat_manager import ChatManager
from ..core.dependencies import get_chat_manager

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
        request: ChatRequest,
        chat_manager: ChatManager = Depends(get_chat_manager)
):
    """Send a message to the AI and get response.

    Args:
        request: ChatRequest with message and options

    Returns:
        ChatResponse with AI message
    """
    logger.info(f"Chat request received: {request.message[:50]}...")

    result = await chat_manager.process_message(
        message=request.message,
        chat_id=request.chat_id,
        temperature=request.temperature,
        system_prompt=request.system_prompt
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))

    return ChatResponse(
        chat_id=result["chat_id"],
        message=result["message"],
        success=True
    )


@router.get("/history/{chat_id}", response_model=ChatHistoryResponse)
async def get_history(
        chat_id: int,
        chat_manager: ChatManager = Depends(get_chat_manager)
):
    """Get full chat history with messages.

    Args:
        chat_id: ID of the chat

    Returns:
        Chat with all messages
    """
    logger.info(f"History request for chat {chat_id}")

    chat = await chat_manager.get_chat_history(chat_id)

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    return ChatHistoryResponse(chat=chat, success=True)


@router.get("/chats", response_model=ChatListResponse)
async def list_chats(
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[str] = None,
        chat_manager: ChatManager = Depends(get_chat_manager)
):
    """List all chats without messages.

    Args:
        limit: Maximum number of chats
        offset: Pagination offset
        user_id: Optional filter by user

    Returns:
        List of chat summaries
    """
    logger.info(f"List chats request: limit={limit}, offset={offset}")

    chats = await chat_manager.get_chats_list(
        limit=limit,
        offset=offset,
        user_id=user_id
    )

    return ChatListResponse(
        chats=chats,
        total=len(chats),
        success=True
    )


@router.delete("/chat/{chat_id}")
async def delete_chat(
        chat_id: int,
        chat_manager: ChatManager = Depends(get_chat_manager)
):
    """Delete a chat and all its messages.

    Args:
        chat_id: ID of the chat to delete

    Returns:
        Success status
    """
    logger.info(f"Delete request for chat {chat_id}")

    deleted = await chat_manager.delete_chat(chat_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Chat not found")

    return {"success": True, "message": f"Chat {chat_id} deleted"}


@router.get("/health", response_model=HealthResponse)
async def health_check(
        chat_manager: ChatManager = Depends(get_chat_manager)
):
    """Health check endpoint.

    Returns:
        Status of all services
    """
    logger.debug("Health check request")

    status = await chat_manager.health_check()

    return HealthResponse(
        status="ok",
        deepseek_api=status["deepseek_api"],
        database=status["database"]
    )