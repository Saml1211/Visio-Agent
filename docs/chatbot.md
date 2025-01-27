## Enhanced Chatbot Features

### Storing Information
To store information to memory, use the `/store` command:
```
/store [content to store]
```

### Fine-Tuning Models
To initiate fine-tuning with conversation history, use:
```
/fine-tune
```

### RAG Function Calls
To perform RAG searches, use:
```
/rag [search query]
```

### Example Usage
```
User: /store The optimal projector placement is 1.5x screen width
Bot: Content successfully stored in memory

User: /rag projector placement
Bot: 1. The optimal projector placement is 1.5x screen width

User: /fine-tune
Bot: Model fine-tuning initiated successfully 
```

## Chatbot Modes

### Action Mode
In Action Mode, the chatbot is optimized for executing commands and performing tasks. To use:
1. Switch to Action Mode: `/mode action`
2. Enter commands like:
   - "Generate BOM report"
   - "Create Visio diagram"
   - "Search RAG memory for [query]"

### Chat Mode
In Chat Mode, the chatbot functions as a general-purpose Q&A assistant. To use:
1. Switch to Chat Mode: `/mode chat`
2. Ask questions or request information:
   - "Explain the difference between HDMI and DisplayPort"
   - "What are the key components of an AV system?"

### Mode Switching
- Use `/mode [action|chat]` to switch modes
- The current mode is displayed in the UI
- Mode persists across sessions 

## Advanced Features

### Auto Mode Switching
The chatbot can automatically switch modes based on your input:
- Commands like "generate" or "create" trigger Action Mode
- Questions starting with "what", "how", etc. trigger Chat Mode
- Disable with `/auto-mode off`

### Help Commands
Get mode-specific help:
```
/help
```

### UI Controls
The chat interface includes:
- Buttons for switching modes
- Visual indicator of current mode
- Help button for mode-specific commands 