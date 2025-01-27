from services.initialization import initialize_services
from services.visio_generation_service import VisioGenerator

async def main():
    # Initialize core services
    services = initialize_services()
    
    # Start Visio Generator with dependencies
    generator = VisioGenerator(
        browserbase=services["browserbase"],
        screenpipe=services["screenpipe"],
        config=services["config"]
    )
    
    await generator.start_services()
    
    # Example usage
    diagram = await generator.generate_diagram({
        "type": "network_diagram",
        "requirements": {...}
    })
    
    diagram.save("network_diagram.vsdx")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 