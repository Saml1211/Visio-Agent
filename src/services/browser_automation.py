from typing import Optional
import logging
from playwright.async_api import async_playwright, Browser, Page

logger = logging.getLogger(__name__)

class HeadlessBrowser:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def init(self):
        """Initialize browser instance"""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
            self.page = await self.browser.new_page()
        except Exception as e:
            logger.error(f"Browser initialization failed: {str(e)}")
            await self.close()
            raise
            
    async def close(self):
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
        except Exception as e:
            logger.error(f"Browser cleanup failed: {str(e)}") 