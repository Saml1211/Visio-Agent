from browserbase import Browser
from screenpipe import PipeClient
from config.service_config import get_config

def initialize_services():
    config = get_config()
    
    # Initialize Browserbase
    browserbase = Browser(
        api_key=config.browserbase_api_key,
        project_id=config.browserbase_project_id,
        headless=True,
        stealth_mode=True
    )
    
    # Initialize Screenpipe
    screenpipe = PipeClient(
        endpoint=config.screenpipe_endpoint,
        api_key=config.screenpipe_api_key
    )
    
    return {
        "browserbase": browserbase,
        "screenpipe": screenpipe,
        "config": config
    } 