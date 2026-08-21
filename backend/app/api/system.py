from fastapi import APIRouter
from app.services.retrieval.qdrant_service import RetrievalService

router = APIRouter()

@router.get("/status")
@router.get("/health")
async def get_status():
    status = "healthy"
    try:
        retriever = RetrievalService()
        # Ping Qdrant
        collections = retriever.client.get_collections()
        qdrant_status = "healthy"
    except Exception as e:
        status = "unhealthy"
        qdrant_status = f"error: {str(e)}"
        
    return {
        "status": status,
        "stt": {"status": "healthy"},
        "vector_index": {"status": qdrant_status},
        "retriever": {"status": "healthy"},
        "generator": {"status": "healthy"},
        "guardrails": {"status": "healthy"}
    }
