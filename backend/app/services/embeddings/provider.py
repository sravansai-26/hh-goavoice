from app.config import settings
import httpx
import os

class EmbeddingProvider:
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError
        
    async def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError

class LocalSentenceTransformerProvider(EmbeddingProvider):
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        try:
            from sentence_transformers import SentenceTransformer
            # Using cpu by default for broad compatibility
            self.model = SentenceTransformer(self.model_name, device="cpu")
        except ImportError:
            raise Exception("sentence-transformers not installed.")
            
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        def _embed():
            return self.model.encode(texts).tolist()
        import asyncio
        return await asyncio.to_thread(_embed)
        
    async def embed_query(self, text: str) -> list[float]:
        def _embed():
            return self.model.encode([text])[0].tolist()
        import asyncio
        return await asyncio.to_thread(_embed)

_provider_instance = None

def get_embedding_provider() -> EmbeddingProvider:
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = LocalSentenceTransformerProvider()
    return _provider_instance
