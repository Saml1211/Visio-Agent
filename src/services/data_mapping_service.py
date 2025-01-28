from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging
import json
import aiofiles
from pathlib import Path
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from .exceptions import ValidationError
from .rag_memory_service import RAGMemoryService

logger = logging.getLogger(__name__)

class MappingType(str, Enum):
    """Types of data mapping operations"""
    COMPONENT = "component"
    CONNECTION = "connection"
    METADATA = "metadata"
    LAYOUT = "layout"

@dataclass
class MappingExample:
    """Example for few-shot learning"""
    source_data: Dict[str, Any]
    target_fields: Dict[str, Any]
    explanation: str
    confidence_score: float
    timestamp: datetime

@dataclass
class MappingResult:
    """Result of a data mapping operation"""
    source_field: str
    target_field: str
    value: Any
    confidence_score: float
    mapping_type: MappingType
    is_manual_override: bool = False
    timestamp: datetime = datetime.now()

class DataMappingService:
    """Service for AI-driven data mapping to Visio fields"""
    
    def __init__(
        self,
        rag_memory: RAGMemoryService,
        examples_dir: Optional[Path] = None,
        model: str = "gpt-4",
        temperature: float = 0.3
    ):
        """Initialize the data mapping service
        
        Args:
            rag_memory: RAG memory service for storing mapping history
            examples_dir: Directory containing mapping examples
            model: LLM model to use
            temperature: LLM temperature setting
        """
        self.rag_memory = rag_memory
        self.examples_dir = examples_dir or Path("config/mapping_examples")
        self.examples_dir.mkdir(parents=True, exist_ok=True)
        self.model = model
        self.temperature = temperature
        
        # Load mapping examples
        self.mapping_examples: Dict[MappingType, List[MappingExample]] = {}
        self.load_mapping_examples()
        
        logger.info(
            f"Initialized DataMappingService with "
            f"{sum(len(examples) for examples in self.mapping_examples.values())} examples"
        )
    
    async def load_mapping_examples(self) -> None:
        """Load mapping examples from files"""
        try:
            for mapping_type in MappingType:
                examples_file = self.examples_dir / f"{mapping_type.value}_examples.json"
                if examples_file.exists():
                    async with aiofiles.open(examples_file, 'r') as f:
                        content = await f.read()
                        examples_data = json.loads(content)
                        
                        self.mapping_examples[mapping_type] = []
                        for example_data in examples_data:
                            example = MappingExample(
                                source_data=example_data["source_data"],
                                target_fields=example_data["target_fields"],
                                explanation=example_data["explanation"],
                                confidence_score=example_data["confidence_score"],
                                timestamp=datetime.fromisoformat(example_data["timestamp"])
                            )
                            self.mapping_examples[mapping_type].append(example)
        
        except Exception as e:
            logger.error(f"Error loading mapping examples: {str(e)}")
            raise ValidationError(f"Failed to load mapping examples: {str(e)}")
    
    async def save_mapping_examples(self, mapping_type: MappingType) -> None:
        """Save mapping examples to file
        
        Args:
            mapping_type: Type of mapping examples to save
        """
        try:
            examples = self.mapping_examples.get(mapping_type, [])
            examples_data = []
            
            for example in examples:
                example_dict = {
                    "source_data": example.source_data,
                    "target_fields": example.target_fields,
                    "explanation": example.explanation,
                    "confidence_score": example.confidence_score,
                    "timestamp": example.timestamp.isoformat()
                }
                examples_data.append(example_dict)
            
            examples_file = self.examples_dir / f"{mapping_type.value}_examples.json"
            async with aiofiles.open(examples_file, 'w') as f:
                await f.write(json.dumps(examples_data, indent=2))
            
            logger.info(f"Saved {len(examples)} mapping examples for {mapping_type.value}")
            
        except Exception as e:
            logger.error(f"Error saving mapping examples: {str(e)}")
            raise ValidationError(f"Failed to save mapping examples: {str(e)}")
    
    def add_mapping_example(
        self,
        mapping_type: MappingType,
        example: MappingExample
    ) -> None:
        """Add a new mapping example
        
        Args:
            mapping_type: Type of mapping
            example: Mapping example to add
        """
        if mapping_type not in self.mapping_examples:
            self.mapping_examples[mapping_type] = []
        
        self.mapping_examples[mapping_type].append(example)
        logger.info(f"Added mapping example for {mapping_type.value}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def map_data(
        self,
        source_data: Dict[str, Any],
        target_schema: Dict[str, Any],
        mapping_type: MappingType
    ) -> List[MappingResult]:
        """Map source data to target fields using LLM
        
        Args:
            source_data: Source data to map
            target_schema: Schema of target fields
            mapping_type: Type of mapping to perform
            
        Returns:
            List of mapping results
        """
        try:
            logger.info(f"Mapping data for {mapping_type.value}")
            
            # Get relevant examples
            examples = self.mapping_examples.get(mapping_type, [])
            
            # Create prompt
            prompt = self._create_mapping_prompt(
                source_data,
                target_schema,
                examples
            )
            
            # Call LLM API
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert in mapping technical data to Visio diagrams."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature
            )
            
            # Parse and validate mappings
            mappings = self._parse_mapping_response(
                response.choices[0].message.content,
                mapping_type
            )
            
            # Store mappings in RAG memory
            await self.rag_memory.store_entry(
                content={
                    "source_data": source_data,
                    "target_schema": target_schema,
                    "mappings": [m.__dict__ for m in mappings]
                },
                metadata={
                    "type": "data_mapping",
                    "mapping_type": mapping_type.value,
                    "model": self.model,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            logger.info(f"Successfully mapped {len(mappings)} fields")
            return mappings
            
        except Exception as e:
            logger.error(f"Error mapping data: {str(e)}")
            raise
    
    def apply_manual_override(
        self,
        mapping_result: MappingResult,
        new_value: Any
    ) -> MappingResult:
        """Apply manual override to a mapping result
        
        Args:
            mapping_result: Original mapping result
            new_value: New value to apply
            
        Returns:
            Updated mapping result
        """
        return MappingResult(
            source_field=mapping_result.source_field,
            target_field=mapping_result.target_field,
            value=new_value,
            confidence_score=1.0,  # Manual override has 100% confidence
            mapping_type=mapping_result.mapping_type,
            is_manual_override=True,
            timestamp=datetime.now()
        )
    
    def _create_mapping_prompt(
        self,
        source_data: Dict[str, Any],
        target_schema: Dict[str, Any],
        examples: List[MappingExample]
    ) -> str:
        """Create prompt for data mapping
        
        Args:
            source_data: Source data to map
            target_schema: Schema of target fields
            examples: Relevant mapping examples
            
        Returns:
            Formatted prompt string
        """
        # Add examples section
        examples_text = "\nExamples of similar mappings:\n"
        for i, example in enumerate(examples[:3], 1):  # Use up to 3 examples
            examples_text += f"\nExample {i}:\n"
            examples_text += f"Source: {json.dumps(example.source_data, indent=2)}\n"
            examples_text += f"Target: {json.dumps(example.target_fields, indent=2)}\n"
            examples_text += f"Explanation: {example.explanation}\n"
        
        return f"""Map the following source data to the target schema fields.
        
Source Data:
{json.dumps(source_data, indent=2)}

Target Schema:
{json.dumps(target_schema, indent=2)}
{examples_text}

Provide mappings in the following JSON format:
{{
    "mappings": [
        {{
            "source_field": "field_name",
            "target_field": "field_name",
            "value": mapped_value,
            "confidence_score": 0.0-1.0,
            "explanation": "Explanation of mapping"
        }}
    ]
}}

Consider:
1. Field name similarities
2. Data type compatibility
3. Semantic meaning
4. Required transformations
5. Confidence in mapping

Provide detailed explanations for non-obvious mappings."""
    
    def _parse_mapping_response(
        self,
        response_content: str,
        mapping_type: MappingType
    ) -> List[MappingResult]:
        """Parse and validate AI mapping response
        
        Args:
            response_content: Raw response from AI
            mapping_type: Type of mapping being performed
            
        Returns:
            List of validated mapping results
            
        Raises:
            ValidationError: If response format is invalid
        """
        try:
            # Parse JSON response
            mapping_data = json.loads(response_content)
            
            # Validate response structure
            if not isinstance(mapping_data, list):
                raise ValidationError("Mapping response must be a list")
                
            mappings = []
            for item in mapping_data:
                # Validate required fields
                if not all(k in item for k in ["source_field", "target_field", "confidence"]):
                    raise ValidationError(
                        "Each mapping must contain source_field, target_field, and confidence"
                    )
                
                # Validate confidence score
                if not isinstance(item["confidence"], (int, float)) or \
                   not 0 <= item["confidence"] <= 1:
                    raise ValidationError("Confidence must be a float between 0 and 1")
                
                # Create validated mapping result
                mapping = MappingResult(
                    source_field=str(item["source_field"]),
                    target_field=str(item["target_field"]),
                    confidence=float(item["confidence"]),
                    mapping_type=mapping_type,
                    metadata=item.get("metadata", {})
                )
                mappings.append(mapping)
            
            return mappings
            
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON in mapping response: {str(e)}")
        except Exception as e:
            raise ValidationError(f"Error parsing mapping response: {str(e)}")

# Limitations:
# 1. No support for complex data transformations
# 2. Limited handling of nested data structures
# 3. No validation of mapped values against target schema
# 4. Basic confidence scoring based on LLM output
# 5. No support for batch mapping operations
# 6. Limited example selection strategy
# 7. No support for bidirectional mapping
# 8. Simple file-based storage of examples 