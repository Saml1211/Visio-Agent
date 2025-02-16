from typing import Dict, Any, List, Optional
import win32com.client
import os
from pathlib import Path
import logging
from ..config.settings import Settings
from ..models.diagram import DiagramComponent, DiagramConnection, Diagram

logger = logging.getLogger(__name__)
settings = Settings()

class DiagramService:
    """Service for managing Visio diagrams."""
    
    def __init__(self):
        self.visio = None
        self.active_diagram = None
        self.stencils = {}
        self._initialize_visio()
        
    def _initialize_visio(self):
        """Initialize the Visio application."""
        try:
            self.visio = win32com.client.Dispatch("Visio.Application")
            self.visio.Visible = True
            self._load_stencils()
            logger.info("Visio application initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Visio: {str(e)}")
            raise
            
    def _load_stencils(self):
        """Load AV system stencils."""
        stencil_path = Path(settings.STENCILS_DIR)
        try:
            for stencil_file in stencil_path.glob("*.vss"):
                stencil_name = stencil_file.stem
                self.stencils[stencil_name] = self.visio.Documents.OpenEx(
                    str(stencil_file),
                    win32com.client.constants.visOpenDocked
                )
            logger.info(f"Loaded {len(self.stencils)} stencils")
        except Exception as e:
            logger.error(f"Failed to load stencils: {str(e)}")
            
    async def create_new_diagram(self) -> str:
        """Create a new Visio diagram."""
        try:
            self.active_diagram = self.visio.Documents.Add("")
            diagram_id = str(self.active_diagram.ID)
            
            # Set up the drawing page with grid and rulers
            page = self.active_diagram.Pages.Item(1)
            page.PageSheet.CellsSRC(
                win32com.client.constants.visSectionObject,
                win32com.client.constants.visGridSpacing,
                win32com.client.constants.visGridXSpacing
            ).ResultIU = 0.25  # 1/4 inch grid
            
            return diagram_id
        except Exception as e:
            logger.error(f"Failed to create new diagram: {str(e)}")
            raise
            
    async def open_diagram(self, file_path: str) -> str:
        """Open an existing Visio diagram."""
        try:
            self.active_diagram = self.visio.Documents.Open(file_path)
            return str(self.active_diagram.ID)
        except Exception as e:
            logger.error(f"Failed to open diagram {file_path}: {str(e)}")
            raise
            
    async def save_diagram(self, file_path: str) -> bool:
        """Save the current diagram."""
        try:
            if self.active_diagram:
                self.active_diagram.SaveAs(file_path)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to save diagram to {file_path}: {str(e)}")
            raise
            
    async def add_component(self, component_type: str, x: float, y: float) -> str:
        """Add a component to the active diagram."""
        try:
            if not self.active_diagram:
                raise ValueError("No active diagram")
                
            page = self.active_diagram.Pages.Item(1)
            master = self._get_component_master(component_type)
            
            if not master:
                raise ValueError(f"Component type {component_type} not found")
                
            shape = page.Drop(master, x, y)
            return str(shape.ID)
        except Exception as e:
            logger.error(f"Failed to add component {component_type}: {str(e)}")
            raise
            
    def _get_component_master(self, component_type: str):
        """Get the master shape for a component type."""
        for stencil in self.stencils.values():
            try:
                return stencil.Masters.ItemU(component_type)
            except:
                continue
        return None
        
    async def connect_components(self, from_id: str, to_id: str, connection_type: str) -> str:
        """Connect two components in the diagram."""
        try:
            if not self.active_diagram:
                raise ValueError("No active diagram")
                
            page = self.active_diagram.Pages.Item(1)
            from_shape = page.Shapes.ItemFromID(int(from_id))
            to_shape = page.Shapes.ItemFromID(int(to_id))
            
            connector = page.Drop(
                self._get_connector_master(connection_type),
                0,
                0
            )
            
            connector.CellsU("BeginX").GlueTo(from_shape.CellsU("PinX"))
            connector.CellsU("EndX").GlueTo(to_shape.CellsU("PinX"))
            
            return str(connector.ID)
        except Exception as e:
            logger.error(f"Failed to connect components: {str(e)}")
            raise
            
    def _get_connector_master(self, connection_type: str):
        """Get the master shape for a connector type."""
        connector_stencil = self.stencils.get("AV_Connectors")
        if connector_stencil:
            return connector_stencil.Masters.ItemU(connection_type)
        return None
        
    async def delete_component(self, component_id: str) -> bool:
        """Delete a component from the diagram."""
        try:
            if not self.active_diagram:
                raise ValueError("No active diagram")
                
            page = self.active_diagram.Pages.Item(1)
            shape = page.Shapes.ItemFromID(int(component_id))
            shape.Delete()
            return True
        except Exception as e:
            logger.error(f"Failed to delete component {component_id}: {str(e)}")
            raise
            
    async def get_diagram_data(self) -> Dict[str, Any]:
        """Get the current diagram data."""
        try:
            if not self.active_diagram:
                return {}
                
            page = self.active_diagram.Pages.Item(1)
            components = []
            connections = []
            
            for shape in page.Shapes:
                if shape.OneD:  # It's a connector
                    connections.append({
                        'id': str(shape.ID),
                        'type': shape.Name,
                        'from_id': str(shape.Connects.Item(1).FromSheet.ID),
                        'to_id': str(shape.Connects.Item(2).FromSheet.ID)
                    })
                else:  # It's a component
                    components.append({
                        'id': str(shape.ID),
                        'type': shape.Name,
                        'x': shape.Cells('PinX').Result(''),
                        'y': shape.Cells('PinY').Result('')
                    })
                    
            return {
                'id': str(self.active_diagram.ID),
                'name': self.active_diagram.Name,
                'components': components,
                'connections': connections
            }
        except Exception as e:
            logger.error(f"Failed to get diagram data: {str(e)}")
            raise
            
    def cleanup(self):
        """Clean up Visio resources."""
        try:
            if self.active_diagram:
                self.active_diagram.Close()
            if self.visio:
                self.visio.Quit()
        except Exception as e:
            logger.error(f"Failed to cleanup Visio resources: {str(e)}") 