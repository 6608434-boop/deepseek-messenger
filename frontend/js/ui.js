/**
 * UI management for DeepSeek Messenger
 * Handles DOM updates and user interface
 */

// DOM elements
const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const newChatButton = document.getElementById('new-chat-button');
const chatList = document.getElementById('chat-list');
const currentChatTitle = document.getElementById('current-chat-title');
const loadingIndicator = document.getElementById('loading-indicator');
const errorToast = document.getElementById('error-toast');

// Current state
let currentChatId = null;

/**
 * Add a message to the chat window
 * @param {string} content - Message text
 * @param {string} role - 'user' or 'assistant'
 * @param {boolean} animate - Whether to animate the message
 */
export function addMessage(content, role, animate = true) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? '👤' : '🤖';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);

    if (animate) {
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(20px)';
        chatMessages.appendChild(messageDiv);

        // Trigger animation
        setTimeout(() => {
            messageDiv.style.transition = 'all 0.3s ease';
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        }, 10);
    } else {
        chatMessages.appendChild(messageDiv);
    }

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Clear all messages from chat window
 */
export function clearMessages() {
    chatMessages.innerHTML = '';
}

/**
 * Show loading indicator
 */
export function showLoading() {
    loadingIndicator.classList.remove('hidden');
    sendButton.disabled = true;
    messageInput.disabled = true;
}

/**
 * Hide loading indicator
 */
export function hideLoading() {
    loadingIndicator.classList.add('hidden');
    sendButton.disabled = false;
    messageInput.disabled = false;
    messageInput.focus();
}

/**
 * Show error message to user
 * @param {string} message - Error message
 */
export function showError(message) {
    errorToast.textContent = message;
    errorToast.classList.remove('hidden');

    // Auto-hide after 5 seconds
    setTimeout(() => {
        errorToast.classList.add('hidden');
    }, 5000);
}

/**
 * Update chat list sidebar
 * @param {Array} chats - List of chats
 * @param {Function} onChatSelect - Callback when chat is selected
 */
export function updateChatList(chats, onChatSelect) {
    chatList.innerHTML = '';

    if (chats.length === 0) {
        const emptyDiv = document.createElement('div');
        emptyDiv.className = 'chat-list-empty';
        emptyDiv.textContent = 'No chats yet';
        chatList.appendChild(emptyDiv);
        return;
    }

    chats.forEach(chat => {
        const chatItem = document.createElement('div');
        chatItem.className = 'chat-list-item';
        if (chat.id === currentChatId) {
            chatItem.classList.add('active');
        }

        const titleDiv = document.createElement('div');
        titleDiv.className = 'chat-item-title';
        titleDiv.textContent = chat.title || 'Untitled';

        const dateDiv = document.createElement('div');
        dateDiv.className = 'chat-item-date';
        dateDiv.textContent = new Date(chat.updated_at).toLocaleDateString();

        chatItem.appendChild(titleDiv);
        chatItem.appendChild(dateDiv);

        chatItem.addEventListener('click', () => {
            onChatSelect(chat.id);
        });

        chatList.appendChild(chatItem);
    });
}

/**
 * Set current chat ID and update UI
 * @param {number} chatId - Chat ID
 * @param {string} title - Chat title
 */
export function setCurrentChat(chatId, title) {
    currentChatId = chatId;
    currentChatTitle.textContent = title || 'New Chat';

    // Update active state in chat list
    document.querySelectorAll('.chat-list-item').forEach(item => {
        item.classList.remove('active');
    });

    const activeItem = Array.from(document.querySelectorAll('.chat-list-item')).find(
        item => item.dataset.chatId === String(chatId)
    );
    if (activeItem) {
        activeItem.classList.add('active');
    }
}

/**
 * Get current chat ID
 * @returns {number|null} Current chat ID
 */
export function getCurrentChatId() {
    return currentChatId;
}

/**
 * Enable/disable input
 * @param {boolean} enabled - Whether input should be enabled
 */
export function setInputEnabled(enabled) {
    messageInput.disabled = !enabled;
    sendButton.disabled = !enabled;

    if (enabled) {
        messageInput.focus();
    }
}

/**
 * Clear input field
 */
export function clearInput() {
    messageInput.value = '';
}

/**
 * Get message from input field
 * @returns {string} Message text
 */
export function getInputMessage() {
    return messageInput.value.trim();
}