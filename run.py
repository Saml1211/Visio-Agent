import uvicorn
from visio_agent import app
from visio_agent.config.settings import Settings

settings = Settings()

if __name__ == "__main__":
    uvicorn.run(
        "visio_agent:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS,
        log_level="info"
    ) 