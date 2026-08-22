import time
from app.config import settings
from google import genai

class TranslationProvider:
    def __init__(self):
        self.api_key = settings.GENERATION_API_KEY
        self.model = "gemini-3.7-flash"
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    async def translate_to_english(self, query: str) -> dict:
        import asyncio
        if not self.client:
            return {"english_query": query, "latency_ms": 0}

        start_time = time.time()
        
        prompt = f"""
Translate the following query into English. If it is already in English, return it exactly as is.
Return ONLY the translation, nothing else, no quotes.
Query: {query}
Translation:
"""
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            english_query = response.text.strip()
            latency_ms = int((time.time() - start_time) * 1000)
            return {"english_query": english_query, "latency_ms": latency_ms}
        except Exception as e:
            # Fallback on failure
            return {"english_query": query, "latency_ms": 0}

translator = TranslationProvider()
