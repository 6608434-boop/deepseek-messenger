/**
 * Main application logic for DeepSeek Messenger
 * Glues together API client and UI manager
 */

import * as api from './api.js';
import * as ui from './ui.js';

// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
    console.log('DeepSeek Messenger initializing...');

    // Check API health
    try {
        const health = await api.healthCheck();
        console.log('API health:', health);
    } catch (error) {
        ui.showError('Cannot connect to server. Make sure backend is running.');
        console.error('Health check failed:', error);
    }

    // Load chat list
    await loadChatList();

    // Setup event listeners
    setupEventListeners();

    // Focus input
    ui.setInputEnabled(true);
});

/**
 * Setup all event listeners
 */
function setupEventListeners() {
    // Send message on button click
    document.getElementById('send-button').addEventListener('click', onSendMessage);

    // Send message on Enter (but allow Shift+Enter for new line)
    document.getElementById('message-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            onSendMessage();
        }
    });

    // New chat button
    document.getElementById('new-chat-button').addEventListener('click', onNewChat);
}

/**
 * Handle send message action
 */
async function onSendMessage() {
    const message = ui.getInputMessage();
    if (!message) return;

    const currentChatId = ui.getCurrentChatId();

    // Add user message to UI immediately
    ui.addMessage(message, 'user');
    ui.clearInput();
    ui.showLoading();

    try {
        // Send to API
        const response = await api.sendMessage(
            message,
            currentChatId,
            0.7  // temperature
        );

        // Add AI response to UI
        ui.addMessage(response.message.content, 'assistant');

        // If this was a new chat, update current chat ID
        if (!currentChatId) {
            ui.setCurrentChat(response.chat_id, message.substring(0, 50));
            await loadChatList();
        }

    } catch (error) {
        console.error('Failed to send message:', error);
        ui.showError('Failed to send message. Check console for details.');
    } finally {
        ui.hideLoading();
    }
}

/**
 * Handle new chat creation
 */
async function onNewChat() {
    ui.clearMessages();
    ui.setCurrentChat(null, 'New Chat');

    // Optional: create empty chat on server
    // For now, just clear UI
}

/**
 * Load chat into UI
 * @param {number} chatId - Chat ID to load
 */
async function loadChat(chatId) {
    ui.showLoading();
    ui.clearMessages();

    try {
        const response = await api.getChatHistory(chatId);

        if (response && response.chat) {
            ui.setCurrentChat(chatId, response.chat.title);

            // Display all messages
            response.chat.messages.forEach(msg => {
                ui.addMessage(msg.content, msg.role, false);
            });
        }
    } catch (error) {
        console.error('Failed to load chat:', error);
        ui.showError('Failed to load chat history');
    } finally {
        ui.hideLoading();
    }
}

/**
 * Load chat list into sidebar
 */
async function loadChatList() {
    try {
        const chats = await api.listChats(50, 0);

        ui.updateChatList(chats, async (chatId) => {
            await loadChat(chatId);
        });
    } catch (error) {
        console.error('Failed to load chat list:', error);
        ui.showError('Failed to load chat list');
    }
}

// Export for debugging
window.app = {
    loadChat,
    loadChatList,
    onNewChat
};