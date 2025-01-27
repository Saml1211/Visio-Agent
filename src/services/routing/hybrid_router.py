class HybridRouter:
    def __init__(self, ai_suggestions, config):
        self.ai_suggestions = ai_suggestions
        self.base_router = OrthogonalRouter(config)
        
    def optimize_path(self, connector):
        # Blend AI suggestions with algorithmic routing
        if connector.id in self.ai_suggestions:
            return self._apply_ai_path(connector)
        return self.base_router.calculate(connector) 