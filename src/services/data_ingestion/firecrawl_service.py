from firecrawl import FirecrawlApp
import json
import os

class FirecrawlService:
    def __init__(self):
        self.client = FirecrawlApp(api_key=os.getenv('FIRECRAWL_API_KEY'))
    
    async def scrape_url(self, url: str, llm_optimized=True) -> dict:
        """Scrape URL with Firecrawl's LLM-optimized output"""
        try:
            params = {
                "url": url,
                "pageOptions": {
                    "includeMarkdown": llm_optimized,
                    "extractScrapedData": True
                }
            }
            result = self.client.scrape(params)
            return {
                "content": result["markdown" if llm_optimized else "html"],
                "metadata": {
                    "firecrawl_processed": True,
                    "llm_optimized": llm_optimized,
                    "entities": result.get("entities", [])
                }
            }
        except Exception as e:
            logger.error(f"Firecrawl failed for {url}: {str(e)}")
            raise 