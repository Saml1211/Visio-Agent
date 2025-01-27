import React, { useState, useCallback } from 'react';
import { ChatMessage } from '../types';

interface ChatbotUIProps {
    onSendMessage: (message: string) => void;
}

const ChatbotUI: React.FC<ChatbotUIProps> = ({ onSendMessage }) => {
    const [mode, setMode] = useState<'action' | 'chat'>('chat');
    const [message, setMessage] = useState('');
    const [messages, setMessages] = useState<ChatMessage[]>([]);

    const handleModeChange = useCallback((newMode: 'action' | 'chat') => {
        setMode(newMode);
        onSendMessage(`/mode ${newMode}`);
    }, [onSendMessage]);

    const handleSendMessage = useCallback(() => {
        if (message.trim()) {
            onSendMessage(message);
            setMessage('');
        }
    }, [message, onSendMessage]);

    return (
        <div className="chatbot-container">
            <div className="mode-selector">
                <button 
                    className={`mode-button ${mode === 'action' ? 'active' : ''}`}
                    onClick={() => handleModeChange('action')}
                    aria-pressed={mode === 'action'}
                >
                    Action Mode
                </button>
                <button 
                    className={`mode-button ${mode === 'chat' ? 'active' : ''}`}
                    onClick={() => handleModeChange('chat')}
                    aria-pressed={mode === 'chat'}
                >
                    Chat Mode
                </button>
            </div>
            
            <div className="messages-container">
                {messages.map((msg, index) => (
                    <div key={index} className={`message ${msg.type}`}>
                        {msg.content}
                    </div>
                ))}
            </div>
            
            <div className="input-container">
                <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder={`${mode === 'action' ? 'Enter a command...' : 'Ask a question...'}`}
                />
                <button 
                    onClick={handleSendMessage}
                    disabled={!message.trim()}
                >
                    Send
                </button>
            </div>
        </div>
    );
};

export default ChatbotUI; 