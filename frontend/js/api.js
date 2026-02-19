/**
 * API client for DeepSeek Messenger
 * Handles all communication with the backend
 */

const API_BASE_URL = 'https://deepseek-messenger-production.up.railway.app/api';

/**
 * Send a message to the AI
 * @param {string} message - User message
 * @param {number|null} chatId - Existing chat ID or null for new chat
 * @param {number} temperature - Creativity (0-1)
 * @returns {Promise<Object>} Response with chat_id and message
 */
export async function sendMessage(message, chatId = null, temperature = 0.7) {
    const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message,
            chat_id: chatId,
            temperature: temperature
        })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to send message');
    }

    return await response.json();
}

/**
 * Get chat history with all messages
 * @param {number} chatId - Chat ID
 * @returns {Promise<Object>} Chat object with messages
 */
export async function getChatHistory(chatId) {
    const response = await fetch(`${API_BASE_URL}/history/${chatId}`);

    if (!response.ok) {
        if (response.status === 404) {
            return null;
        }
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get chat history');
    }

    return await response.json();
}

/**
 * Get list of all chats (without messages)
 * @param {number} limit - Maximum number of chats
 * @param {number} offset - Pagination offset
 * @returns {Promise<Array>} List of chats
 */
export async function listChats(limit = 50, offset = 0) {
    const response = await fetch(`${API_BASE_URL}/chats?limit=${limit}&offset=${offset}`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to list chats');
    }

    const data = await response.json();
    return data.chats || [];
}

/**
 * Delete a chat
 * @param {number} chatId - Chat ID to delete
 * @returns {Promise<boolean>} True if deleted
 */
export async function deleteChat(chatId) {
    const response = await fetch(`${API_BASE_URL}/chat/${chatId}`, {
        method: 'DELETE'
    });

    if (!response.ok) {
        if (response.status === 404) {
            return false;
        }
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete chat');
    }

    return true;
}

/**
 * Check API health
 * @returns {Promise<Object>} Health status
 */
export async function healthCheck() {
    const response = await fetch(`${API_BASE_URL}/health`);

    if (!response.ok) {
        throw new Error('API is not available');
    }

    return await response.json();
}