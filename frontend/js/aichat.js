// AI Chat functionality
// Authentication is handled by navbar.js

let conversationHistory = [];

document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');
    const sendButton = document.getElementById('sendButton');

    if (chatForm) {
        chatForm.addEventListener('submit', handleChatSubmit);
    }

    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleChatSubmit(e);
            }
        });
    }
});

async function handleChatSubmit(e) {
    e.preventDefault();
    
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');
    const sendButton = document.getElementById('sendButton');
    
    const message = chatInput.value.trim();
    if (!message) return;
    
    // Add user message to chat
    addMessageToChat('user', message);
    
    // Clear input and disable send button
    chatInput.value = '';
    if (sendButton) sendButton.disabled = true;
    
    try {
        // Add thinking indicator
        const thinkingId = addMessageToChat('assistant', 'Thinking...', true);
        
        // Call AI chat API
        const response = await API.apiCall('aiChat', {
            method: 'POST',
            body: JSON.stringify({
                message: message,
                context: conversationHistory.slice(-5) // Last 5 messages for context
            })
        });
        
        // Remove thinking indicator
        removeMessage(thinkingId);
        
        // Add AI response
        addMessageToChat('assistant', response.response);
        
        // Update conversation history
        conversationHistory.push(
            { role: 'user', content: message },
            { role: 'assistant', content: response.response }
        );
        
    } catch (error) {
        console.error('Chat error:', error);
        addMessageToChat('assistant', 'Sorry, I encountered an error. Please try again.');
    } finally {
        if (sendButton) sendButton.disabled = false;
        chatInput.focus();
    }
}

function addMessageToChat(role, content, isTemporary = false) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    const messageId = 'msg-' + Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.id = messageId;
    messageDiv.className = `message ${role}-message${isTemporary ? ' temporary' : ''}`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.textContent = content;
    
    const messageTime = document.createElement('div');
    messageTime.className = 'message-time';
    messageTime.textContent = new Date().toLocaleTimeString();
    
    messageDiv.appendChild(messageContent);
    messageDiv.appendChild(messageTime);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageId;
}

function removeMessage(messageId) {
    const message = document.getElementById(messageId);
    if (message) {
        message.remove();
    }
}
