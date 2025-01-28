from multi_agent_orchestrator import Agent, Message

class VisioGenerationAgent(Agent):
    def __init__(self, visio_service):
        super().__init__("visio_generator")
        self.visio_service = visio_service
        
    async def process(self, message: Message) -> Message:
        """Handle diagram generation requests"""
        try:
            vsdx_path = self.visio_service.generate_diagram(message.content)
            return Message.success(
                content={"path": vsdx_path},
                context=message.context
            )
        except Exception as e:
            return Message.error(
                error=f"Generation failed: {str(e)}",
                context=message.context
            )

class ValidationAgent(Agent):
    def __init__(self, quality_rules):
        super().__init__("validation_engine")
        self.quality_rules = quality_rules
        
    async def process(self, message: Message) -> Message:
        """Perform multi-level validation"""
        # Existing validation logic
        return Message.success(...) 