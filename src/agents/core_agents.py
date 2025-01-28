from multi_agent_orchestrator import Agent, Message
from langchain.tools import tool
from typing import Optional, Dict, Any

class DocumentProcessingAgent(Agent):
    def __init__(self, processor):
        super().__init__("document_processor")
        self.processor = processor
        
    async def process(self, message: Message) -> Message:
        try:
            processed = await self.processor.run_pipeline(message.content)
            return Message.success(
                content=processed,
                context=message.context
            )
        except Exception as e:
            return Message.error(
                error=f"Document processing failed: {str(e)}",
                context=message.context
            )

class VisioGenerationAgent(Agent):
    def __init__(self, visio_service):
        super().__init__("visio_generator")
        self.visio_service = visio_service
        self.template_manager = VisioTemplateManager()
        
    async def process(self, message: Message) -> Message:
        try:
            # Get template with fallback
            template = message.content.get("template")
            if not self.template_manager.validate_template(template):
                template = self.template_manager.get_default_template()
                
            # Generate diagram
            result = self.visio_service.generate_diagram(
                components=message.content["components"],
                template=template
            )
            
            return Message.success(
                content={"diagram_path": result},
                context=message.context
            )
        except Exception as e:
            return Message.error(
                error=f"Visio generation failed: {str(e)}",
                context=message.context
            )

class ComplianceAgent(Agent):
    def __init__(self, validator):
        super().__init__("compliance_validator")
        self.validator = validator
        
    async def process(self, message: Message) -> Message:
        try:
            report = await self.validator.full_validation(
                diagram_path=message.content["diagram_path"],
                spec_version=message.content.get("spec_version", "CTS-4.0")
            )
            return Message.success(
                content=report.dict(),
                context=message.context
            )
        except Exception as e:
            return Message.error(
                error=f"Compliance check failed: {str(e)}",
                context=message.context
            )

@tool
def handle_visio_errors(error: dict) -> Optional[Dict[str, Any]]:
    """Attempt automatic recovery from Visio COM errors"""
    try:
        from .visio_recovery import recover_from_com_error
        return recover_from_com_error(error)
    except Exception as e:
        logger.error(f"Recovery attempt failed: {str(e)}")
        return None 