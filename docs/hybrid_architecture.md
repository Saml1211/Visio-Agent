# Hybrid Architecture Documentation

## Overview
The Visio Agent uses a hybrid architecture combining React and NiceGUI to provide a rich, interactive user experience. This document outlines the architecture, integration points, and best practices for development.

## Architecture Components

### 1. Frontend Architecture
```
frontend/
├── src/
│   ├── hybrid/
│   │   ├── NiceguiWrapper.tsx      # React wrapper for NiceGUI components
│   │   ├── types/                  # TypeScript types for hybrid components
│   │   └── hooks/                  # Custom hooks for state management
│   └── app/
│       ├── tools/                  # React routes for NiceGUI tools
│       └── shared/                 # Shared components and utilities
```

### 2. Backend Architecture
```
src/
├── services/
│   └── gui_service.py             # HybridGUI service integration
├── models/
│   └── shared_state.py            # Shared state management
└── assets/
    └── hybrid.css                 # Shared styling variables
```

## Integration Points

### 1. State Management
The hybrid architecture uses a dual-state management approach:

```python
# Backend (shared_state.py)
class SharedState(BaseModel):
    user_id: UUID
    state: Dict[str, Any]
    last_update: Optional[str]
```

```typescript
// Frontend (types/shared-state.ts)
interface SharedState {
  userId: string;
  state: {
    currentDiagram?: DiagramState;
    pipelineStatus?: PipelineStatus;
  };
  lastUpdate?: string;
}
```

### 2. WebSocket Communication
Real-time updates are handled through Socket.IO:

```python
# Backend (gui_service.py)
@self.sio.on('state_update')
async def handle_state_update(sid, data):
    self.shared_state.update(data)
    await self.sio.emit('state_changed', self.shared_state)
```

```typescript
// Frontend (NiceguiWrapper.tsx)
socketRef.current.on('state_changed', (newState) => {
  onStateChange?.(newState);
});
```

## Authentication Flow

1. **JWT Authentication**
   - Tokens are shared between React and NiceGUI
   - All WebSocket connections require authentication
   - Token refresh is handled by the React frontend

```python
# Backend authentication middleware
@app.middleware("http")
async def authenticate_requests(request: Request, call_next):
    if request.url.path.startswith("/tools/"):
        token = request.headers.get("Authorization")
        # Validate JWT token
        user = await validate_token(token)
        request.state.user = user
    return await call_next(request)
```

## Routing Structure

### 1. React Routes (`/app/*`)
- Main application interface
- User dashboard
- Project management
- Settings

### 2. NiceGUI Routes (`/tools/*`)
- Real-time Visio preview (`/tools/preview`)
- Admin dashboard (`/tools/admin`)
- Pipeline monitor (`/tools/pipeline`)

## Styling Integration

The hybrid architecture uses shared CSS variables for consistent styling:

```css
/* hybrid.css */
:root {
  --primary-color: #3182ce;
  --background-color: #f7fafc;
  /* ... other variables ... */
}
```

## Development Guidelines

### 1. Adding New Tools

1. Create the NiceGUI page:
```python
@ui.page('/tools/new-tool')
async def new_tool(user: User = Depends(get_current_user)):
    with ui.card():
        ui.label('New Tool').classes('text-xl font-bold')
        # Add tool components
```

2. Create the React wrapper:
```typescript
export const NewTool: React.FC = () => {
  return (
    <NiceguiWrapper
      toolPath="new-tool"
      className="min-h-[600px]"
    />
  );
};
```

### 2. State Synchronization

When adding new state:

1. Update the SharedState model:
```python
class SharedState(BaseModel):
    new_feature: Optional[Dict[str, Any]]
```

2. Add TypeScript types:
```typescript
interface SharedState {
  newFeature?: {
    [key: string]: any;
  };
}
```

### 3. Error Handling

```python
@ui.page('/tools/preview')
async def preview_tool(user: User = Depends(get_current_user)):
    try:
        with ui.card():
            # Tool implementation
    except Exception as e:
        logger.error("Preview tool error", error=str(e))
        ui.notify(f"Error: {str(e)}", type="error")
```

## Performance Considerations

1. **Lazy Loading**
   - Use React.lazy for tool components
   - Load NiceGUI resources on demand

2. **WebSocket Optimization**
   - Implement message debouncing
   - Use binary data for large payloads
   - Compress SVG content

3. **State Management**
   - Cache shared state where appropriate
   - Implement state versioning
   - Use optimistic updates

## Testing Strategy

### 1. Unit Tests
```python
# test_gui_service.py
async def test_state_update():
    gui = HybridGUI(app)
    await gui.handle_state_update("test-sid", {"key": "value"})
    assert gui.shared_state["key"] == "value"
```

### 2. Integration Tests
```typescript
// NiceguiWrapper.test.tsx
test('wrapper handles state updates', async () => {
  render(<NiceguiWrapper toolPath="preview" />);
  // Test WebSocket communication
});
```

## Security Considerations

1. **CORS Configuration**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

2. **WebSocket Security**
- Validate all incoming messages
- Implement rate limiting
- Use secure WebSocket connections (wss://)

## Troubleshooting Guide

### Common Issues

1. **WebSocket Connection Failures**
   - Check CORS configuration
   - Verify token authentication
   - Ensure proper SSL setup

2. **State Synchronization Issues**
   - Check WebSocket event handlers
   - Verify state update propagation
   - Monitor browser console for errors

3. **Styling Inconsistencies**
   - Verify CSS variable inheritance
   - Check iframe style injection
   - Inspect computed styles

## Deployment Considerations

1. **Environment Configuration**
```bash
# .env
REACT_APP_API_URL=https://api.example.com
NICEGUI_HOST=0.0.0.0
NICEGUI_PORT=8000
```

2. **Docker Configuration**
```dockerfile
# Dockerfile
FROM python:3.10
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "src/main.py"]
```

## Monitoring and Logging

1. **WebSocket Monitoring**
```python
@self.sio.on('connect')
async def connect(sid, environ):
    logger.info("Client connected", sid=sid, environ=environ)
```

2. **Performance Metrics**
```python
async def log_performance_metrics():
    metrics = {
        "connected_clients": len(self.sio.eio.sockets),
        "state_size": len(json.dumps(self.shared_state))
    }
    logger.info("Performance metrics", **metrics)
``` 