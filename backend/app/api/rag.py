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
    if retrieval_guard["status"] == "FAIL":
        if lang_name.lower() == "telugu":
            no_evi_ans = "ఈ ప్రశ్నకు సమాధానం ఇవ్వడానికి తగిన ఆధారాలు నాకు లభించలేదు."
        elif lang_name.lower() == "hindi":
            no_evi_ans = "मुझे इस प्रश्न का उत्तर देने के लिए पर्याप्त प्रमाण नहीं मिले हैं।"
        elif lang_name.lower() == "tamil":
            no_evi_ans = "இந்தக் கேள்விக்குப் பதிலளிக்க போதுமான ஆதாரங்கள் கிடைக்கவில்லை."
        else:
            no_evi_ans = "I do not have enough evidence to answer this question."

        latencies["total_ms"] = int((time.time() - start_time) * 1000)
        return RAGResponse(
            success=False,
            language={"detected": lang_code, "name": lang_name},
            query={"original": req.query, "english": english_query},
            answer={"primary": no_evi_ans, "english": "I don't have enough evidence in the retrieved sources to answer this question."},
            sources=retrieved_chunks,
            grounded=False,
            guardrail=retrieval_guard,
            retrieval={"strategy": req.strategy, "top_k": req.top_k, "results_count": len(retrieved_chunks)},
            latency=latencies
        )
        
    # 4. Generation
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
    gen_guard = guardrails.validate_generation(gen_res.get("answer_primary", ""), gen_res.get("grounded", False))
    success = gen_guard["status"] == "PASS"
    
    from app.services.telemetry import log_metrics
    log_metrics(latencies, success)
    
    if not success:
        gen_res["answer_primary"] = f"FAILED: {gen_guard['reason']}"
        gen_res["answer_english"] = "Generation failed safety checks."
    
    return RAGResponse(
        success=success,
        language={"detected": lang_code, "name": lang_name},
        query={"original": req.query, "english": english_query},
        answer={"primary": gen_res["answer_primary"], "english": gen_res["answer_english"]},
        sources=retrieved_chunks,
        grounded=gen_res.get("grounded", False),
        guardrail=gen_guard,
        retrieval={"strategy": req.strategy, "top_k": req.top_k, "results_count": len(retrieved_chunks)},
        latency=latencies
    )
