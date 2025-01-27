from collections import defaultdict
from typing import List, Dict
from dependency_injector import providers, containers
import asyncio
from .ai_services import BaseAIService
from .deepseek_service import DeepSeekService
from .gemini_service import GeminiService
from .openai_service import OpenAIService

class LLMOrchestrator:
    def __init__(self, services: Dict[str, BaseAIService]):
        self.services = services
        self.active_models = ['deepseek', 'gemini', 'openai']
        
    async def generate_diagram(self, document: str) -> dict:
        tasks = []
        for model in self.active_models:
            if service := self.services.get(model):
                tasks.append(
                    self._execute_model(service, document)
                )
                
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return self._consensus_analysis(results)

    async def _execute_model(self, service: BaseAIService, document: str) -> dict:
        try:
            start = time.monotonic()
            result = await service.process(document)
            return {
                'model': service.name,
                'result': result,
                'latency': time.monotonic() - start,
                'error': None
            }
        except Exception as e:
            return {'model': service.name, 'error': str(e)}

    def _consensus_analysis(self, results: List[dict]) -> dict:
        # Add model quality weights from config
        quality_weights = {
            'deepseek': 0.9,
            'gemini': 0.85,
            'openai': 0.88
        }
        
        component_votes = defaultdict(float)
        for res in results:
            weight = quality_weights.get(res['model'], 0.8) * res['result'].get('confidence', 0.7)
            for component in res['result']['components']:
                component_votes[component['id']] += weight
        
        # Dynamic threshold based on number of models
        threshold = max(1.0, len(results) * 0.6)
        return [cid for cid, score in component_votes.items() if score >= threshold]

class AIServiceContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    
    deepseek = providers.Factory(
        DeepSeekService,
        api_key=config.deepseek.api_key,
        model=config.deepseek.model
    )
    
    gemini = providers.Factory(
        GeminiService,
        api_key=config.gemini.api_key
    )
    
    openai = providers.Factory(
        OpenAIService,
        api_key=config.openai.api_key
    )
    
    orchestrator = providers.Factory(
        LLMOrchestrator,
        services={
            'deepseek': deepseek,
            'gemini': gemini,
            'openai': openai
        }
    ) 