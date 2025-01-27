from browserbase import Browser, Script
import os
from httpx import AsyncClient, Limits

class SpecSearch:
    def __init__(self):
        self.browser = Browser(
            headless=True,
            api_key=os.getenv('BROWSERBASE_KEY')
        )
        self.search_templates = {
            'network_gear': 'https://specs.net/search?q=',
            'av_equipment': 'https://avspecs.pro/search?'
        }
        self.client = AsyncClient(
            limits=Limits(max_connections=100, max_keepalive_connections=20),
            timeout=30.0
        )
    
    async def get_specs(self, component_type: str, model: str) -> dict:
        """Search across multiple spec databases"""
        url = self.search_templates.get(component_type, self.search_templates['default'])
        script = Script(f"""
            navigate("{url}{model}")
            wait_for_selector(".specifications", timeout=15000)
            return {{
                specs: parse_spec_table(),
                images: get_image_urls(),
                docs: get_related_docs()
            }}
        """)
        
        response = await self.client.get(url)
        return response.json() 