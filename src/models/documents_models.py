from typing import TypedDict, Literal
from datetime import datetime

class ProcessedContent(TypedDict):
    raw_text: str
    structured_data: dict
    entities: list[dict]
    confidence_score: float
    processing_metadata: dict[str, datetime | str]

class ValidationIssue(TypedDict):
    message: str
    severity: Literal['low', 'medium', 'high']
    location: str
    timestamp: datetime 