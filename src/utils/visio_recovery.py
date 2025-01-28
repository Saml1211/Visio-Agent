class VisioErrorHandler:
    def __init__(self):
        self.recovery_attempts = 0
        self.max_retries = 3
        
    async def handle_com_error(self, error: win32com.client.pywintypes.com_error):
        """Advanced COM error recovery"""
        try:
            if self.recovery_attempts < self.max_retries:
                # Release stuck COM objects
                win32com.client.pythoncom.CoFreeUnusedLibraries()
                
                # Reset Visio instance
                self.visio_app.Quit()
                self.visio_app = win32com.client.Dispatch("Visio.Application")
                
                # Clear temporary files
                for temp_file in Path("temp").glob("*.vsdx"):
                    temp_file.unlink()
                    
                self.recovery_attempts += 1
                return True
            return False
        except Exception as e:
            logger.error(f"Critical recovery failure: {str(e)}")
            raise VisioFatalError("Unrecoverable COM error") 