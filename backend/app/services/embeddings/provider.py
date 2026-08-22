from app.config import settings
import httpx
import os

class EmbeddingProvider:
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError
        
    async def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError

class HFInferenceEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/{self.model_name}"
        self.headers = {}
        hf_token = os.getenv("HF_TOKEN")
        if hf_token:
            self.headers["Authorization"] = f"Bearer {hf_token}"

    async def _call_api(self, inputs):
        async with httpx.AsyncClient() as client:
            response = await client.post(self.api_url, headers=self.headers, json={"inputs": inputs})
            response.raise_for_status()
            return response.json()

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self._call_api(texts)
        
    async def embed_query(self, text: str) -> list[float]:
        result = await self._call_api([text])
        return result[0]

_provider_instance = None

def get_embedding_provider() -> EmbeddingProvider:
    global _provider_instance
    if _provider_instance is None:
        # Default to HF Inference API to save RAM on Render Free Tier
        _provider_instance = HFInferenceEmbeddingProvider()
    return _provider_instance
