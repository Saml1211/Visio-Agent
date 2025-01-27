from vertexai.preview.generative_models import GenerativeModel
from typing import Dict, Any, Optional
import os
import logging
from .service_interfaces import AIService

logger = logging.getLogger(__name__)

class VertexAIService(AIService):
    def __init__(self, config: Dict[str, Any]):
        self.project = config['project_id']
        self.location = config.get('location', 'us-central1')
        self.model_map = config['model_map']
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Vertex AI client with proper credentials"""
        from google.auth import default
        
        credentials, _ = default()
        self.client = GenerativeModel(
            project=self.project,
            location=self.location,
            credentials=credentials
        )
        logger.info(f"Initialized Vertex AI client for project {self.project}")

    async def analyze_content(self, content: str, context: Dict) -> Dict:
        model_name = self.model_map.get('analyze_content', 'gemini-pro')
        try:
            model = GenerativeModel(model_name)
            response = await model.generate_content_async(
                f"{content}\n\nContext: {json.dumps(context)}"
            )
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"Vertex AI analysis error: {str(e)}")
            raise

    async def generate_text(self, prompt: str, parameters: Dict) -> str:
        model_name = self.model_map.get('text_generation', 'gemini-pro')
        try:
            model = GenerativeModel(model_name)
            response = await model.generate_content_async(
                prompt,
                generation_config=self._create_generation_config(parameters)
            )
            return response.text
        except Exception as e:
            logger.error(f"Vertex AI generation error: {str(e)}")
            raise

    def _create_generation_config(self, parameters: Dict) -> Dict:
        return {
            "temperature": parameters.get('temperature', 0.2),
            "top_p": parameters.get('top_p', 0.95),
            "max_output_tokens": parameters.get('max_tokens', 2048)
        }

    def _parse_response(self, response) -> Dict:
        return {
            "content": response.text,
            "safety_ratings": {
                category: rating.value
                for category, rating in response.candidates[0].safety_ratings.items()
            },
            "citations": [
                {
                    "source": cit.source,
                    "license": cit.license
                }
                for cit in response.candidates[0].citation_metadata.citations
            ]
        } 