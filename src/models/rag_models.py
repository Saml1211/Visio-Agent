from pydantic import BaseModel, validator
from typing import Dict, Any

class DocumentSchema(BaseModel):
    name: str
    fields: Dict[str, Dict[str, Any]]
    
    @validator('fields')
    def validate_fields(cls, fields):
        required = [name for name, config in fields.items() if config.get('required')]
        if not required:
            raise ValueError("Schema must contain at least one required field")
        return fields

class LLDDocumentSchema(DocumentSchema):
    class Config:
        schema_extra = {
            "name": "LLD Document",
            "fields": {
                "component_type": {"type": "string", "required": True},
                "interfaces": {"type": "list", "required": True}
            }
        } 