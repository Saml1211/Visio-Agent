from pydantic import BaseModel, Field, confloat, conint, validator
from typing import Literal, Optional, List, Dict, Union
from enum import Enum

class RGBColor(BaseModel):
    r: conint(ge=0, le=255) = 0
    g: conint(ge=0, le=255) = 0
    b: conint(ge=0, le=255) = 0

class PageDimensions(BaseModel):
    width: Union[float, str] = Field(..., description="Width in mm or Visio units")
    height: Union[float, str] = Field(..., description="Height in mm or Visio units")

class PageMargins(BaseModel):
    top: Union[float, str]
    bottom: Union[float, str]
    left: Union[float, str]
    right: Union[float, str]

class BackgroundElements(BaseModel):
    presence: bool = True
    type: Literal['gradient', 'pattern', 'image']
    description: str
    opacity: confloat(ge=0.0, le=1.0) = 1.0

class FontStyle(BaseModel):
    family: str = "Arial"
    size: Union[float, str] = Field(..., description="Size in points")
    weight: Literal['normal', 'bold', 'light'] = 'normal'
    style: Literal['normal', 'italic'] = 'normal'
    color: RGBColor = RGBColor()
    alignment: Literal['left', 'center', 'right', 'justify'] = 'left'

class LineStyle(BaseModel):
    weight: Union[float, str]
    type: Literal['solid', 'dash', 'dot', 'dash_dot', 'dash_dot_dot', 'dotted']
    color: RGBColor
    pattern: Optional[str] = None
    start_arrow: Optional[str] = None
    end_arrow: Optional[str] = None

class ShapeStyle(BaseModel):
    fill_color: RGBColor
    fill_opacity: confloat(ge=0.0, le=1.0) = 1.0
    outline_style: LineStyle
    effects: Dict[str, Union[str, float]] = Field(default_factory=dict)

class ColorScheme(BaseModel):
    primary: RGBColor
    secondary: RGBColor
    accent: RGBColor
    background: RGBColor
    text: RGBColor
    highlight: RGBColor

class LayoutRules(BaseModel):
    grid_columns: conint(ge=1, le=12) = 3
    spacing: Union[float, str]
    alignment: Literal['start', 'center', 'end', 'stretch']
    padding: Union[float, str]

class ImageStyle(BaseModel):
    max_width: Union[float, str]
    max_height: Union[float, str]
    border_style: LineStyle
    caption_style: FontStyle

class ComplexRule(BaseModel):
    selector: str
    styles: Dict[str, Union[str, float, RGBColor, Dict]]
    media_queries: Optional[Dict[str, Dict]] = None

class PageSettingsRules(BaseModel):
    dimensions: PageDimensions
    orientation: Literal['portrait', 'landscape']
    margins: PageMargins
    background: BackgroundElements
    grid_snap: bool = True
    ruler_visibility: bool = True

class TitleBlockRules(BaseModel):
    logo_position: Dict[str, Union[float, str]]
    info_block_styles: Dict[str, FontStyle]
    revision_table: Dict[str, Union[FontStyle, LineStyle]]

# Additional models for other rule types...

class FontRules(BaseModel):
    family: str = "Arial"
    size: conint(ge=6, le=72) = 11
    color: RGBColor = RGBColor()
    weight: Literal['normal', 'bold'] = 'normal'
    style: Literal['normal', 'italic'] = 'normal'
    alignment: Literal['left', 'center', 'right'] = 'left'

class ShapeRules(BaseModel):
    fill: RGBColor = RGBColor(r=240, g=240, b=240)
    border: RGBColor = RGBColor(r=89, g=89, b=89)
    radius: conint(ge=0, le=20) = 2
    shadow: Dict[str, float] = {'opacity': 0, 'offset_x': 0.1, 'offset_y': 0.1}
    rotation: conint(ge=0, le=359) = 0

class PageRules(BaseModel):
    dimensions: Dict[str, float] = {'width': 11.0, 'height': 8.5}
    margins: Dict[str, float] = {'top': 0.5, 'bottom': 0.5, 'left': 0.5, 'right': 0.5}
    background: RGBColor = RGBColor(r=255, g=255, b=255) 