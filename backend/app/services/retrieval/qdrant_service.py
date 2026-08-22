from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.services.embeddings.provider import get_embedding_provider
import time

class RetrievalService:
    def __init__(self, collection_name: str = "msmarco_xi_chunks"):
        from app.config import settings
        if settings.QDRANT_MODE == "cloud" and settings.clean_qdrant_url:
            self.client = QdrantClient(url=settings.clean_qdrant_url, api_key=settings.QDRANT_API_KEY)
        else:
            self.client = QdrantClient(path="local_qdrant")
        self.collection_name = collection_name
        self.embedder = get_embedding_provider()
        
    async def retrieve(self, query: str, strategy: str = "fixed", top_k: int = 5, language: str = None) -> dict:
        start_time = time.time()
        
        try:
            # 1. Embed query
            query_vector = await self.embedder.embed_query(query)
        except Exception as e:
            raise Exception(f"Embedding Failed: {str(e)}")
            
        # 2. Prepare filter (optional: by strategy and language)
        must_conditions = []
        if strategy:
            must_conditions.append(FieldCondition(key="strategy", match=MatchValue(value=strategy)))

            
        query_filter = Filter(must=must_conditions) if must_conditions else None
        
        try:
            # 3. Search
            search_result = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=query_filter,
                limit=top_k
            )
        except Exception as e:
            raise Exception(f"Qdrant Search Failed: {str(e)}")
        
        # 4. Format results
        results = []
        for scored_point in search_result.points:
            payload = scored_point.payload
            results.append({
                "chunk_id": payload.get("chunk_id"),
                "document_id": payload.get("document_id"),
                "text": payload.get("text"),
                "score": scored_point.score,
                "metadata": payload.get("metadata", {})
            })
            
        latency_ms = int((time.time() - start_time) * 1000)
        return {
            "results": results,
            "latency_ms": latency_ms
        }
