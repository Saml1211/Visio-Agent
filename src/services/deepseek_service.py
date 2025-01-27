import asyncio
import re
import json
from deepseek_service.exceptions import APIConnectionError, InvalidResponseError

class DeepSeekService:
    def __init__(self, client, model, logger):
        self.client = client
        self.model = model
        self.logger = logger

    async def _call_api(self, prompt: str, retries: int = 3) -> dict:
        for attempt in range(retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }],
                    temperature=0.7,
                    max_tokens=2000
                )
                return response.choices[0].message.content
            except APIConnectionError as e:
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
            
    def _parse_response(self, raw_response: str) -> dict:
        try:
            # Extract JSON from markdown code block
            json_str = re.search(r'```json\n(.*?)\n```', raw_response, re.DOTALL).group(1)
            return json.loads(json_str)
        except (AttributeError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to parse response: {str(e)}")
            raise InvalidResponseError("Malformed API response") 