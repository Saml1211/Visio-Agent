from screenpipe import PipeClient, ContentType

class VisioContextEnricher:
    def __init__(self):
        self.pipe = PipeClient()
        self.active_context = {}
        
    async def start(self):
        await self.pipe.subscribe(
            content_types=[ContentType.OCR, ContentType.APP_STATE],
            callback=self.update_context
        )
    
    def get_design_context(self):
        """Get current relevant design parameters"""
        return {
            'components': self.active_context.get('last_components', []),
            'current_app': self.active_context.get('focused_app', ''),
            'recent_specs': self.active_context.get('spec_history', [])
        }
    
    async def update_context(self, update):
        if update.content_type == ContentType.OCR:
            self.active_context['last_ocr'] = update.data
            self.active_context['last_components'] = self.extract_components(update.data)
        elif update.content_type == ContentType.APP_STATE:
            self.active_context.update(update.data) 
    
    async def capture_design_session(self):
        """Record full design session context"""
        return await self.pipe.capture_session(
            include_types=[ContentType.OCR, ContentType.APP_STATE],
            duration=60*30  # 30 minute session
        )
    
    def get_active_component(self):
        """Get component under cursor using Screenpipe AI"""
        return self.pipe.query_ai("""
            Analyze current Visio selection and return:
            - Component type
            - Critical specs needed
            - Related components
        """) 