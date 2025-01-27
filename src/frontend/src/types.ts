export interface ChatMessage {
    content: string;
    type: 'user' | 'bot';
    timestamp: Date;
} 