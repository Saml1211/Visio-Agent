import logging
from typing import Dict, List, Optional, Any
import openai
from tenacity import retry, stop_after_attempt, wait_exponential
import json
from datetime import datetime
from pydantic_settings import BaseSettings
import re

from src.models.document_models import ProcessedContent, AVComponent
from src.services.service_interfaces import AIService
from src.services.rag_memory_service import RAGMemoryService
from src.services.self_learning_service import SelfLearningService, FeedbackEntry

logger = logging.getLogger(__name__)

# Common words to filter out in keyword extraction
COMMON_WORDS = {
    "the", "and", "for", "with", "that", "this", "from", "have", "will", "what",
    "when", "where", "who", "which", "why", "how", "all", "any", "both", "each"
}

class Prompt:
    def __init__(self, content: str, version: str):
        self.content = content
        self.version = version

class AIServiceConfig(BaseSettings):
    api_key: str
    model: str = "gpt-4"
    temperature: float = 0.7

class LLMBasedAIService(AIService):
    """Service for interacting with LLM-based AI providers.
    
    Attributes:
        api_key (str): API key for the AI provider.
        model (str): Model to use for AI calls.
        temperature (float): Temperature parameter for AI calls.
    """
    
    def __init__(
        self,
        api_key: str,
        rag_service: RAGMemoryService,
        self_learning_service: SelfLearningService,
        model: str = "gpt-4",
        temperature: float = 0.7
    ):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.rag_service = rag_service
        self.self_learning_service = self_learning_service
        openai.api_key = api_key
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extracts keywords from text for RAG queries"""
        # This is a simple implementation - could be made more sophisticated
        words = text.lower().split()
        # Filter common words and keep relevant technical terms
        keywords = [w for w in words if len(w) > 3 and w not in COMMON_WORDS]
        return list(set(keywords))[:10]  # Return top 10 unique keywords
    
    def _create_analysis_prompt(
        self,
        content: ProcessedContent,
        relevant_knowledge: List[Dict]
    ) -> str:
        """Creates prompt for content analysis with RAG context"""
        knowledge_context = "\n\nRelevant past analyses:\n"
        for entry in relevant_knowledge:
            knowledge_context += f"- {entry.entry.content}\n"
        
        return f"""
        Analyze the following AV system technical content and extract key information:
        
        Raw Text:
        {content.raw_text}
        
        Existing Structured Data:
        {content.structured_data}
        {knowledge_context}
        
        Please identify:
        1. All AV components and their specifications
        2. Technical requirements and constraints
        3. Any potential issues or missing information
        4. Confidence level for each extracted piece of information
        
        Use the relevant past analyses to improve accuracy and consistency.
        Provide the analysis in a structured JSON format.
        """
    
    def _create_relationship_prompt(
        self,
        entities: List[Dict],
        relevant_knowledge: List[Dict]
    ) -> str:
        """Creates prompt for relationship mapping with RAG context"""
        knowledge_context = "\n\nRelevant past mappings:\n"
        for entry in relevant_knowledge:
            knowledge_context += f"- {entry.entry.content}\n"
        
        return f"""
        Map the relationships between the following AV components:
        
        Components:
        {entities}
        {knowledge_context}
        
        For each component, identify:
        1. Input connections
        2. Output connections
        3. Signal types
        4. Connection requirements
        5. Any potential compatibility issues
        
        Use the relevant past mappings to improve accuracy and consistency.
        Provide the relationships in a structured JSON format.
        """
    
    def _create_layout_prompt(
        self,
        components: List[AVComponent],
        relevant_knowledge: List[Dict]
    ) -> str:
        """Creates prompt for layout planning with RAG context"""
        knowledge_context = "\n\nRelevant past layouts:\n"
        for entry in relevant_knowledge:
            knowledge_context += f"- {entry.entry.content}\n"
        
        return f"""
        Plan the optimal layout for the following AV components in a Visio diagram:
        
        Components:
        {[comp.__dict__ for comp in components]}
        {knowledge_context}
        
        Consider:
        1. Logical grouping of components
        2. Signal flow direction
        3. Connection complexity
        4. Visual clarity and readability
        5. Standard AV diagram conventions
        
        Use the relevant past layouts to improve placement and routing.
        Provide the layout plan in a structured JSON format including:
        1. Component positions
        2. Connection routing
        3. Layout optimization suggestions
        """
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def analyze_content(self, processed_content):
        """Analyzes technical content using LLM with RAG enhancement"""
        try:
            return await self._call_openai(processed_content)
        except Exception as e:
            logger.error("OpenAI API failed: %s", str(e))
            return self._fallback_analysis(processed_content)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def map_relationships(self, entities: List[Dict]) -> List[Dict]:
        """Maps relationships between AV components with RAG enhancement"""
        try:
            logger.info(f"Mapping relationships between {len(entities)} entities")
            
            # Retrieve relevant knowledge
            context = {
                "entity_types": list(set(e.get("type") for e in entities)),
                "component_count": len(entities)
            }
            
            relevant_knowledge = await self.self_learning_service.retrieve_relevant_knowledge(
                context=context,
                feedback_type="relationship_mapping"
            )
            
            # Prepare the prompt with RAG context
            prompt = self._create_relationship_prompt(entities, relevant_knowledge)
            
            # Call LLM API
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert in AV system connectivity."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature
            )
            
            # Parse and validate relationships
            relationships = self._parse_relationship_response(response.choices[0].message.content)
            
            # Store the relationships in RAG memory
            await self.rag_service.store_project_knowledge(
                project_id=entities[0].get("project_id", "unknown"),
                content={"relationships": relationships},
                metadata={
                    "type": "relationship_mapping",
                    "model": self.model,
                    "entity_count": len(entities)
                }
            )
            
            logger.info(f"Mapped {len(relationships)} relationships")
            return relationships
            
        except Exception as e:
            logger.error(f"Error mapping relationships: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def plan_layout(self, components: List[AVComponent]) -> Dict:
        """Plans optimal layout for Visio diagram with RAG enhancement"""
        try:
            logger.info(f"Planning layout for {len(components)} components")
            
            # Retrieve relevant knowledge
            context = {
                "component_types": list(set(c.type for c in components)),
                "component_count": len(components)
            }
            
            relevant_knowledge = await self.self_learning_service.retrieve_relevant_knowledge(
                context=context,
                feedback_type="layout_planning"
            )
            
            # Prepare the prompt with RAG context
            prompt = self._create_layout_prompt(components, relevant_knowledge)
            
            # Call LLM API
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert in AV system diagram layout."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature
            )
            
            # Parse and validate layout plan
            layout_plan = self._parse_layout_response(response.choices[0].message.content)
            
            # Store the layout plan in RAG memory
            await self.rag_service.store_project_knowledge(
                project_id=components[0].id.split("_")[0],  # Assuming project ID is part of component ID
                content=layout_plan,
                metadata={
                    "type": "layout_planning",
                    "model": self.model,
                    "component_count": len(components)
                }
            )
            
            logger.info("Layout planning completed successfully")
            return layout_plan
            
        except Exception as e:
            logger.error(f"Error planning layout: {str(e)}")
            raise
    
    async def process_feedback(
        self,
        feedback_type: str,
        input_data: Dict[str, Any],
        expected_output: Dict[str, Any],
        actual_output: Dict[str, Any],
        user_feedback: str,
        confidence_score: float
    ) -> str:
        """Processes user feedback for model improvement"""
        try:
            feedback_id = f"feedback_{datetime.now().timestamp()}"
            feedback = FeedbackEntry(
                id=feedback_id,
                feedback_type=feedback_type,
                input_data=input_data,
                expected_output=expected_output,
                actual_output=actual_output,
                user_feedback=user_feedback,
                confidence_score=confidence_score
            )
            
            # Store feedback in RAG memory
            await self.rag_service.store_entry(
                content=feedback.dict(),
                metadata={"type": "feedback", "feedback_type": feedback_type},
                entry_type="feedback"
            )
            
            # Trigger model improvement if needed
            if self._should_improve_model(feedback):
                await self._trigger_model_improvement(feedback)
            
            return feedback_id
            
        except Exception as e:
            logger.error(f"Error processing feedback: {str(e)}")
            raise
    
    def _parse_analysis_response(self, response: str) -> Dict:
        """Parses and validates LLM response for content analysis"""
        try:
            # Add response parsing logic here
            # This is a placeholder implementation
            return {
                "entities": [],
                "issues": [],
                "suggestions": [],
                "confidence_score": 0.9
            }
        except Exception as e:
            logger.error(f"Error parsing analysis response: {str(e)}")
            raise
    
    def _parse_relationship_response(self, response: str) -> List[Dict]:
        """Parses and validates LLM response for relationship mapping"""
        try:
            # Add response parsing logic here
            # This is a placeholder implementation
            return []
        except Exception as e:
            logger.error(f"Error parsing relationship response: {str(e)}")
            raise
    
    def _parse_layout_response(self, response: str) -> Dict:
        """Parses and validates LLM response for layout planning"""
        try:
            # Add response parsing logic here
            # This is a placeholder implementation
            return {
                "layout": {},
                "issues": [],
                "suggestions": [],
                "confidence_score": 0.9
            }
        except Exception as e:
            logger.error(f"Error parsing layout response: {str(e)}")
            raise

def sanitize_input(input_str: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\s\-_]", "", input_str) 