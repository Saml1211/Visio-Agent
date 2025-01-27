from screenpipe import PipeClient
from browserbase import Browser, Script

class TechSpecsService:
    def __init__(self):
        self.pipe = PipeClient()
        self.browser = Browser()
        self.spec_cache = {}
        
    async def start(self):
        # Subscribe to screenpipe events
        await self.pipe.subscribe(
            event_types=['ocr_update', 'app_focus'],
            callback=self.handle_context_change
        )
        
    async def handle_context_change(self, event):
        """Use screen context to drive spec searches"""
        if event.type == 'ocr_update':
            components = self.extract_components(event.content)
            await self.fetch_specs(components)
            
        elif event.type == 'app_focus' and 'visio' in event.app_name:
            current_design = self.analyze_active_design()
            await self.fetch_related_specs(current_design)

    async def fetch_specs(self, components: list):
        """Browserbase-powered spec retrieval"""
        for component in components:
            if component not in self.spec_cache:
                script = Script(f"""
                    navigate("https://techspecs.site/search?q={component}")
                    wait_for_selector(".spec-table")
                    return get_page_content()
                """)
                result = await self.browser.run(script)
                self.spec_cache[component] = self.parse_specs(result)
        
        return self.spec_cache[component]

    def extract_components(self, ocr_text: str) -> list:
        """Use LLM to identify technical components"""
        return self.llm_analyze(f"""
            Identify technical components from this design document:
            {ocr_text}
            Return only component model numbers as comma-separated list.
        """)

    async def get_3d_specs(self, model: str):
        """Retrieve 3D product dimensions"""
        return await self.browser.run(Script(f"""
            navigate("https://3dspecs.pro/model/{model}")
            wait_for_selector("#3d-viewer")
            return {{
                dimensions: get_3d_measurements(),
                ports: get_port_locations(),
                mounting_points: get_mounting_specs()
            }}
        """))
    
    async def get_compatibility(self, component_a: str, component_b: str):
        """Check component compatibility"""
        result = await self.browser.run(Script(f"""
            navigate("https://compatibilitycheck.com/{component_a}/{component_b}")
            return {{
                compatible: !!document.querySelector(".compatible"),
                issues: get_compatibility_issues()
            }}
        """))
        return result 