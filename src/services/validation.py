from pydantic import BaseModel, Field
from typing import List, Dict, Any

class ComponentExtractorInput(BaseModel):
    text: str = Field(..., min_length=1)

class SpecsFetcherInput(BaseModel):
    model_url: str = Field(..., regex=r'^https?://')

class DiagramInput(BaseModel):
    components: List[Dict[str, Any]] = Field(..., min_items=1)
    layout: str = Field(..., regex=r'^(auto|manual|grid)$') 