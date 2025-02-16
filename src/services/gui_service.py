from fastapi import FastAPI, Depends
from nicegui import ui
from typing import Dict, Any, Optional
from pydantic import BaseModel
from ..security.auth import get_current_user
from ..models.user import User
from ..models.shared_state import SharedState
import asyncio
import socketio
import logging
from pathlib import Path
import json
from ..config.settings import Settings

logger = logging.getLogger(__name__)
settings = Settings()

class GUIService:
    """Service for managing NiceGUI interfaces."""
    
    def __init__(self, shared_state: SharedState):
        self.shared_state = shared_state
        self.tools: Dict[str, Any] = {}
        self._load_tool_configs()
        self.sio = socketio.AsyncServer(async_mode='asgi')
        self.setup_websocket()
        
    def _load_tool_configs(self) -> None:
        """Load tool configurations from JSON files."""
        tool_config_path = Path(__file__).parent.parent / "config" / "tools"
        if tool_config_path.exists():
            for config_file in tool_config_path.glob("*.json"):
                try:
                    tool_name = config_file.stem
                    with open(config_file) as f:
                        self.tools[tool_name] = json.load(f)
                except Exception as e:
                    logger.error(f"Error loading tool config {config_file}: {e}")
    
    async def render_main_page(self) -> None:
        """Render the main application page."""
        # Configure page
        ui.page.title = settings.NICEGUI_TITLE
        ui.page.dark = settings.NICEGUI_DARK_MODE
        
        # Create layout
        with ui.header().classes('bg-primary text-white'):
            ui.label(settings.NICEGUI_TITLE).classes('text-h6')
            with ui.row().classes('items-center'):
                for tool in settings.AVAILABLE_TOOLS:
                    ui.link(
                        tool.replace('_', ' ').title(),
                        f'/tools/{tool}'
                    ).classes('text-white mx-2')
        
        with ui.column().classes('w-full p-4'):
            with ui.card().classes('w-full'):
                ui.label('Welcome to Visio Agent').classes('text-h5 q-mb-md')
                ui.label(
                    'Select a tool from the header to get started with your AV system diagrams.'
                ).classes('text-body1')
            
            with ui.row().classes('w-full q-mt-md'):
                for tool in settings.AVAILABLE_TOOLS:
                    with ui.card().classes('w-1/4 m-2'):
                        ui.label(tool.replace('_', ' ').title()).classes('text-h6')
                        ui.label(self.tools.get(tool, {}).get('description', 'Tool description...'))
                        ui.link(
                            'Open Tool',
                            f'/tools/{tool}'
                        ).classes('q-mt-sm')
        
        # Add footer
        with ui.footer().classes('bg-primary text-white'):
            ui.label('© 2025 Visio Agent').classes('text-caption')
    
    async def render_tool_page(self, tool_name: str) -> None:
        """Render a specific tool page."""
        if tool_name not in settings.AVAILABLE_TOOLS:
            with ui.column().classes('w-full p-4'):
                ui.label('Tool not found').classes('text-h5 text-negative')
                ui.link('Return to Home', '/').classes('q-mt-md')
            return
        
        # Configure page
        ui.page.title = f"{settings.NICEGUI_TITLE} - {tool_name.replace('_', ' ').title()}"
        ui.page.dark = settings.NICEGUI_DARK_MODE
        
        # Create layout
        with ui.header().classes('bg-primary text-white'):
            with ui.row().classes('items-center'):
                ui.link(settings.NICEGUI_TITLE, '/').classes('text-h6 text-white')
                ui.label(f'/ {tool_name.replace("_", " ").title()}').classes('text-subtitle1')
        
        # Get tool state
        tool_state = await self.shared_state.get_tool_state(tool_name) or {}
        
        # Render tool-specific content
        with ui.column().classes('w-full p-4'):
            await self._render_tool_content(tool_name, tool_state)
    
    async def _render_tool_content(self, tool_name: str, tool_state: Dict[str, Any]) -> None:
        """Render tool-specific content."""
        tool_config = self.tools.get(tool_name, {})
        
        with ui.card().classes('w-full'):
            ui.label(tool_name.replace('_', ' ').title()).classes('text-h5')
            ui.label(tool_config.get('description', 'Tool description...')).classes('text-body1 q-mb-md')
            
            # Render tool-specific components based on the tool name
            if tool_name == "diagram_editor":
                await self._render_diagram_editor(tool_state)
            elif tool_name == "component_library":
                await self._render_component_library(tool_state)
            elif tool_name == "system_analyzer":
                await self._render_system_analyzer(tool_state)
            elif tool_name == "document_processor":
                await self._render_document_processor(tool_state)
    
    async def _render_diagram_editor(self, tool_state: Dict[str, Any]) -> None:
        """Render the diagram editor tool."""
        with ui.column().classes('w-full'):
            with ui.row().classes('w-full q-mb-md'):
                ui.button('New Diagram', on_click=self.new_diagram_handler).classes('q-mr-sm')
                ui.button('Open Diagram', on_click=self.open_diagram_handler).classes('q-mr-sm')
                ui.button('Save Diagram', on_click=self.save_diagram_handler)
            
            with ui.row().classes('w-full'):
                # Left sidebar for components
                with ui.column().classes('w-1/4'):
                    ui.label('Components').classes('text-h6')
                    # Add component palette here
                
                # Main drawing area
                with ui.column().classes('w-3/4'):
                    ui.label('Drawing Area').classes('text-h6')
                    # Add drawing canvas here
    
    async def _render_component_library(self, tool_state: Dict[str, Any]) -> None:
        """Render the component library tool."""
        with ui.column().classes('w-full'):
            with ui.row().classes('w-full q-mb-md'):
                ui.button('Add Component', on_click=self.add_component_handler).classes('q-mr-sm')
                ui.button('Import Components', on_click=self.import_components_handler)
            
            with ui.row().classes('w-full'):
                # Component grid
                for i in range(6):  # Placeholder components
                    with ui.card().classes('w-1/3 m-2'):
                        ui.label(f'Component {i+1}').classes('text-h6')
                        ui.label('Component description...')
    
    async def _render_system_analyzer(self, tool_state: Dict[str, Any]) -> None:
        """Render the system analyzer tool."""
        with ui.column().classes('w-full'):
            with ui.row().classes('w-full q-mb-md'):
                ui.button('Analyze System', on_click=self.analyze_system_handler).classes('q-mr-sm')
                ui.button('Export Report', on_click=self.export_report_handler)
            
            with ui.tabs().classes('w-full') as tabs:
                ui.tab('Overview')
                ui.tab('Analysis')
                ui.tab('Reports')
            
            with ui.tab_panels(tabs, value='Overview').classes('w-full'):
                with ui.tab_panel('Overview'):
                    ui.label('System Overview').classes('text-h6')
                with ui.tab_panel('Analysis'):
                    ui.label('Analysis Results').classes('text-h6')
                with ui.tab_panel('Reports'):
                    ui.label('Generated Reports').classes('text-h6')
    
    async def _render_document_processor(self, tool_state: Dict[str, Any]) -> None:
        """Render the document processor tool."""
        with ui.column().classes('w-full'):
            with ui.row().classes('w-full q-mb-md'):
                ui.button('Upload Document', on_click=self.upload_document_handler).classes('q-mr-sm')
                ui.button('Process Documents', on_click=self.process_documents_handler).classes('q-mr-sm')
                ui.button('Export Results', on_click=self.export_results_handler)
            
            with ui.row().classes('w-full'):
                # Document list
                with ui.column().classes('w-1/3'):
                    ui.label('Documents').classes('text-h6')
                    # Add document list here
                
                # Preview and results
                with ui.column().classes('w-2/3'):
                    ui.label('Preview').classes('text-h6')
                    # Add document preview here

    def setup_websocket(self):
        @self.sio.on('connect')
        async def connect(sid, environ):
            logger.info(f'Client connected: {sid}')
            
        @self.sio.on('disconnect')
        async def disconnect(sid):
            logger.info(f'Client disconnected: {sid}')
            
        @self.sio.on('state_update')
        async def handle_state_update(sid, data):
            """Handle state updates from React frontend"""
            self.shared_state.update(data)
            await self.sio.emit('state_changed', self.shared_state)

    async def new_diagram_handler(self):
        import uuid
        new_id = str(uuid.uuid4())
        self.shared_state.tool_states['diagram_editor'] = {'diagram': 'new', 'id': new_id}
        ui.notify(f'New diagram created with id {new_id}')

    async def open_diagram_handler(self):
        self.shared_state.tool_states['diagram_editor'] = {'diagram': 'opened', 'id': 'diagram_opened'}
        ui.notify('Diagram opened.')

    async def save_diagram_handler(self):
        ui.notify('Diagram saved.')

    async def add_component_handler(self):
        ui.notify('Component added.')

    async def import_components_handler(self):
        ui.notify('Components imported.')

    async def analyze_system_handler(self):
        ui.notify('System analysis started.')
        import asyncio
        await asyncio.sleep(1)
        ui.notify('System analysis complete.')

    async def export_report_handler(self):
        ui.notify('Report exported.')

    async def upload_document_handler(self):
        ui.notify('Document uploaded.')

    async def process_documents_handler(self):
        ui.notify('Document processing started.')
        import asyncio
        await asyncio.sleep(1)
        ui.notify('Document processing complete.')

    async def export_results_handler(self):
        ui.notify('Results exported.') 