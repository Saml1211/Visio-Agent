# Hybrid Architecture Quick Start Guide

## Prerequisites
- Python 3.10+
- Node.js 16+
- npm or yarn
- Git

## Setup

### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd visio-agent

# Install Python dependencies
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Install Node.js dependencies
cd frontend
npm install
```

### 2. Environment Configuration

Create a `.env` file in the root directory:

```bash
# Backend settings
DEBUG=true
HOST=localhost
PORT=8000
CORS_ORIGINS=["http://localhost:3000"]
JWT_SECRET=your-secret-key

# Frontend settings (.env in frontend directory)
REACT_APP_API_URL=http://localhost:8000
```

### 3. Start Development Servers

```bash
# Terminal 1: Start backend
python src/main.py

# Terminal 2: Start frontend
cd frontend
npm start
```

## Quick Examples

### 1. Create a New Tool

#### Backend (src/services/gui_service.py):
```python
@ui.page('/tools/my-tool')
async def my_tool(user: User = Depends(get_current_user)):
    with ui.card().classes('w-full'):
        ui.label('My Tool').classes('text-xl font-bold')
        
        # Add interactive elements
        counter = ui.number()
        
        def on_click():
            counter.value += 1
            
        ui.button('Increment', on_click=on_click)
```

#### Frontend (src/frontend/src/tools/MyTool.tsx):
```typescript
import { NiceguiWrapper } from '../hybrid/NiceguiWrapper';

export const MyTool: React.FC = () => {
  return (
    <div className="h-screen">
      <NiceguiWrapper
        toolPath="my-tool"
        className="min-h-[400px]"
      />
    </div>
  );
};
```

### 2. Add State Management

#### Backend:
```python
from models.shared_state import SharedState

@self.sio.on('update_tool_state')
async def handle_tool_update(sid, data):
    self.shared_state['my_tool'] = data
    await self.sio.emit('tool_state_changed', self.shared_state['my_tool'])
```

#### Frontend:
```typescript
const MyTool: React.FC = () => {
  const handleStateChange = (newState: any) => {
    console.log('Tool state updated:', newState);
  };

  return (
    <NiceguiWrapper
      toolPath="my-tool"
      onStateChange={handleStateChange}
    />
  );
};
```

## Common Tasks

### 1. Add a New Route

```typescript
// src/frontend/src/App.tsx
import { MyTool } from './tools/MyTool';

function App() {
  return (
    <Routes>
      <Route path="/tools/my-tool" element={<MyTool />} />
    </Routes>
  );
}
```

### 2. Handle Authentication

```typescript
// src/frontend/src/hybrid/NiceguiWrapper.tsx
const { getToken, isAuthenticated } = useAuth();

useEffect(() => {
  if (!isAuthenticated) {
    navigate('/login');
    return;
  }
  
  const token = getToken();
  // Setup WebSocket with authentication
}, [isAuthenticated]);
```

### 3. Add Error Handling

```python
# Backend
from fastapi import HTTPException

@ui.page('/tools/my-tool')
async def my_tool(user: User = Depends(get_current_user)):
    try:
        # Tool implementation
        pass
    except Exception as e:
        logger.error("Tool error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
```

```typescript
// Frontend
const MyTool: React.FC = () => {
  const [error, setError] = useState<string | null>(null);

  return (
    <div>
      {error && (
        <Alert status="error">{error}</Alert>
      )}
      <NiceguiWrapper
        toolPath="my-tool"
        onError={setError}
      />
    </div>
  );
};
```

## Development Tips

1. **Hot Reload**
   - Backend supports hot reload with `uvicorn`
   - Frontend uses React's hot module replacement

2. **Debugging**
   - Use browser dev tools for WebSocket inspection
   - Check Python logs for backend issues
   - Use React Developer Tools for component debugging

3. **Testing**
   ```bash
   # Run backend tests
   pytest tests/

   # Run frontend tests
   cd frontend
   npm test
   ```

## Common Issues and Solutions

### 1. CORS Errors
```python
# Ensure CORS is properly configured in main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. WebSocket Connection Issues
```typescript
// Add error handling to socket connection
socketRef.current = io(process.env.REACT_APP_API_URL, {
  reconnection: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 1000,
});

socketRef.current.on('connect_error', (error) => {
  console.error('WebSocket connection error:', error);
});
```

### 3. State Synchronization Issues
```python
# Add logging to track state updates
@self.sio.on('state_update')
async def handle_state_update(sid, data):
    logger.info("State update received", sid=sid, data=data)
    self.shared_state.update(data)
    await self.sio.emit('state_changed', self.shared_state)
```

## Next Steps

1. Review the full [Architecture Documentation](./hybrid_architecture.md)
2. Explore example tools in `src/services/gui_service.py`
3. Check out the test suite in `tests/`
4. Join the developer community on Discord 