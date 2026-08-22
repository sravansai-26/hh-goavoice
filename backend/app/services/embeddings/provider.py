from app.config import settings
import httpx
import os

class EmbeddingProvider:
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError
        
    async def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError

class GeminiEmbeddingProvider(EmbeddingProvider):
    def __init__(self):
        from google import genai
        from app.config import settings
        self.client = genai.Client(api_key=settings.GENERATION_API_KEY)
        self.model = "gemini-embedding-2"
        
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        def _embed():
            result = self.client.models.embed_content(
                model=self.model,
                contents=texts
            )
            return [e.values for e in result.embeddings]
        import asyncio
        return await asyncio.to_thread(_embed)
        
    async def embed_query(self, text: str) -> list[float]:
        def _embed():
            result = self.client.models.embed_content(
                model=self.model,
                contents=text
            )
            return result.embeddings[0].values
        import asyncio
        return await asyncio.to_thread(_embed)

_provider_instance = None

def get_embedding_provider() -> EmbeddingProvider:
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = GeminiEmbeddingProvider()
    return _provider_instance
