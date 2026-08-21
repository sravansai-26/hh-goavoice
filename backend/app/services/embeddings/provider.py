from app.config import settings

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
            raise Exception("sentence-transformers not installed. Install it or use an external provider.")
            
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # This is blocking, in a real async FastAPI app we'd run this in a threadpool
        # But for the hackathon/simplicity, we just call it directly.
        embeddings = self.model.encode(texts)
        return embeddings.tolist()
        
    async def embed_query(self, text: str) -> list[float]:
        embedding = self.model.encode([text])[0]
        return embedding.tolist()

_provider_instance = None

def get_embedding_provider() -> EmbeddingProvider:
    global _provider_instance
    if _provider_instance is None:
        if settings.EMBEDDING_PROVIDER == "local":
            _provider_instance = LocalSentenceTransformerProvider()
        else:
            _provider_instance = LocalSentenceTransformerProvider()
    return _provider_instance
