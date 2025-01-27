import asyncio
from typing import List, Optional
from firecrawl import FirecrawlClient
from redis import Redis
import json
import logging

logger = logging.getLogger(__name__)

class SpecCrawler:
    def __init__(self, api_key: str, redis_url: str):
        self.client = FirecrawlClient(api_key)
        self.redis = Redis.from_url(redis_url)
        self.cache_ttl = 86400  # 24 hours
        logger.info("SpecCrawler initialized")
        
    async def get_component_specs(self, manufacturer: str, model: str) -> Optional[dict]:
        cache_key = f"specs:{manufacturer}:{model}"
        
        # Check cache first
        cached = self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
            
        try:
            specs = await self.client.crawl_product_specs(
                manufacturer=manufacturer,
                model=model,
                include_datasheets=True
            )
            
            if specs:
                # Cache the results
                self.redis.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(specs)
                )
                return specs
                
        except Exception as e:
            logger.error(f"Crawl failed for {manufacturer} {model}: {str(e)}")
            return None
            
    async def batch_crawl_specs(self, components: List[dict]) -> dict:
        tasks = []
        for comp in components:
            if comp.get('manufacturer') and comp.get('model'):
                tasks.append(self.get_component_specs(
                    comp['manufacturer'],
                    comp['model']
                ))
                
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            comp['id']: result for comp, result in zip(components, results)
            if not isinstance(result, Exception)
        } 