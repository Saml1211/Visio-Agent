from tenacity import retry, wait_exponential, stop_after_attempt

def jina_retry(max_retries=3):
    return retry(
        wait=wait_exponential(multiplier=1, max=10),
        stop=stop_after_attempt(max_retries),
        reraise=True
    ) 