from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import time

from app.services.retrieval.qdrant_service import RetrievalService
from app.services.generation.generator import get_generation_provider
from app.services.guardrails import get_guardrails_service

router = APIRouter()
retriever = RetrievalService()
generator = get_generation_provider()
guardrails = get_guardrails_service()

class RAGRequest(BaseModel):
    query: str
    strategy: str = "fixed"
    top_k: int = 5
    language: str = "hi" # Defaults to Hindi based on dev set

class RAGResponse(BaseModel):
    success: bool
    query: str
    answer: str
    sources: list
    grounded: bool
    guardrail: dict
    retrieval: dict
    latency: dict

@router.post("/query", response_model=RAGResponse)
async def process_rag_query(req: RAGRequest):
    start_time = time.time()
    latencies = {}
    
    # 1. Validation (Guardrail: Query relevance / basic check)
    val_start = time.time()
    query_guard = guardrails.validate_query(req.query)
    latencies["validation_ms"] = int((time.time() - val_start) * 1000)
    
    if query_guard["status"] == "FAIL":
        return RAGResponse(
            success=False,
            query=req.query,
            answer=f"REFUSED: {query_guard['reason']}",
            sources=[],
            grounded=False,
            guardrail=query_guard,
            retrieval={"strategy": req.strategy, "top_k": req.top_k, "results_count": 0},
            latency=latencies
        )
    
    # 2. Retrieval
    try:
        retrieval_res = await retriever.retrieve(
            query=req.query,
            strategy=req.strategy,
            top_k=req.top_k,
            language=req.language
        )
        latencies["retrieval_ms"] = retrieval_res["latency_ms"]
        # Add embedding time (it's inside retrieve right now)
        latencies["embedding_ms"] = 0
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")
        
    retrieved_chunks = retrieval_res["results"]
    
    # Guardrail: Retrieval sufficiency
    retrieval_guard = guardrails.validate_retrieval(retrieved_chunks)
    if retrieval_guard["status"] == "FAIL":
        return RAGResponse(
            success=False,
            query=req.query,
            answer="INSUFFICIENT_EVIDENCE",
            sources=retrieved_chunks,
            grounded=False,
            guardrail=retrieval_guard,
            retrieval={"strategy": req.strategy, "top_k": req.top_k, "results_count": len(retrieved_chunks)},
            latency=latencies
        )
        
    # 3. Generation
    try:
        gen_res = await generator.generate(
            query=req.query,
            context=retrieved_chunks,
            language=req.language
        )
        latencies["generation_ms"] = gen_res["latency_ms"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
        
    latencies["grounding_ms"] = 0 # Included in generation for now
    latencies["total_ms"] = int((time.time() - start_time) * 1000)
    
    # 4. Guardrail: Generation & Grounding formulation
    gen_guard = guardrails.validate_generation(gen_res.get("answer", ""), gen_res.get("grounded", False))
    success = gen_guard["status"] == "PASS"
    
    from app.services.telemetry import log_metrics
    log_metrics(latencies, success)
    
    return RAGResponse(
        success=success,
        query=req.query,
        answer=gen_res["answer"] if success else f"FAILED: {gen_guard['reason']}",
        sources=retrieved_chunks,
        grounded=gen_res.get("grounded", False),
        guardrail=gen_guard,
        retrieval={"strategy": req.strategy, "top_k": req.top_k, "results_count": len(retrieved_chunks)},
        latency=latencies
    )
