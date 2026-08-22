from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import time

from app.services.retrieval.qdrant_service import RetrievalService
from app.services.generation.generator import get_generation_provider
from app.services.guardrails import get_guardrails_service
from app.services.translation import translator
from app.config_languages import get_language_name

router = APIRouter()
retriever = RetrievalService()
generator = get_generation_provider()
guardrails = get_guardrails_service()

class RAGRequest(BaseModel):
    query: str
    strategy: str = "fixed"
    top_k: int = 5
    language: str = "hi" 
    english_query: str = None

class RAGResponse(BaseModel):
    success: bool
    language: dict
    query: dict
    answer: dict
    sources: list
    grounded: bool
    guardrail: dict
    retrieval: dict
    latency: dict

@router.post("/query", response_model=RAGResponse)
async def process_rag_query(req: RAGRequest):
    start_time = time.time()
    latencies = {}
    
    lang_code = req.language
    lang_name = get_language_name(lang_code)
    
    # 1. Translation (Bridge to English)
    if not req.english_query:
        if lang_code == "en":
            english_query = req.query
            latencies["translation_ms"] = 0
        else:
            trans_res = await translator.translate_to_english(req.query)
            english_query = trans_res["english_query"]
            latencies["translation_ms"] = trans_res["latency_ms"]
    else:
        english_query = req.english_query
        latencies["translation_ms"] = 0
    
    # 2. Validation (Guardrail: Query relevance / basic check)
    val_start = time.time()
    query_guard = guardrails.validate_query(req.query)
    latencies["validation_ms"] = int((time.time() - val_start) * 1000)
    
    if query_guard["status"] == "FAIL":
        return RAGResponse(
            success=False,
            language={"detected": lang_code, "name": lang_name},
            query={"original": req.query, "english": english_query},
            answer={"primary": f"REFUSED: {query_guard['reason']}", "english": "Query refused by guardrails."},
            sources=[],
            grounded=False,
            guardrail=query_guard,
            retrieval={"strategy": req.strategy, "top_k": req.top_k, "results_count": 0},
            latency=latencies
        )
    
    # 3. Retrieval
    try:
        retrieval_res = await retriever.retrieve(
            query=req.query,
            strategy=req.strategy,
            top_k=req.top_k,
            language=lang_code
        )
        latencies["retrieval_ms"] = retrieval_res["latency_ms"]
        latencies["embedding_ms"] = 0
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")
        
    retrieved_chunks = retrieval_res["results"]
    
    # Guardrail: Retrieval sufficiency
    retrieval_guard = guardrails.validate_retrieval(retrieved_chunks)
    
    # 4. Generation
    # We still generate the answer even if retrieval failed, to show the user the model's knowledge,
    # but the guardrails will mark it as FAILED / UNGROUNDED.
    try:
        gen_res = await generator.generate(
            query=req.query,
            english_query=english_query,
            context=retrieved_chunks,
            language_name=lang_name
        )
        latencies["generation_ms"] = gen_res["latency_ms"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
        
    latencies["grounding_ms"] = 0
    latencies["total_ms"] = int((time.time() - start_time) * 1000)
    
    # 5. Guardrail: Generation & Grounding formulation
    # If retrieval was insufficient, force grounded=False
    if retrieval_guard["status"] == "FAIL":
        gen_res["grounded"] = False
        
    gen_guard = guardrails.validate_generation(gen_res.get("answer_primary", ""), gen_res.get("grounded", False))
    success = gen_guard["status"] == "PASS"
    
    from app.services.telemetry import log_metrics
    log_metrics(latencies, success)
    
    # DO NOT overwrite the answer with "FAILED". The user wants to see the actual answer,
    # while the UI correctly shows the "FAIL" badge for grounding.
    
    return RAGResponse(
        success=success,
        language={"detected": lang_code, "name": lang_name},
        query={"original": req.query, "english": english_query},
        answer={"primary": gen_res.get("answer_primary", ""), "english": gen_res.get("answer_english", "")},
        sources=retrieved_chunks,
        grounded=gen_res.get("grounded", False),
        guardrail=gen_guard,
        retrieval={"strategy": req.strategy, "top_k": req.top_k, "results_count": len(retrieved_chunks)},
        latency=latencies
    )
