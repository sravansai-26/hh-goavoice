from typing import List, Dict, Any

class GuardrailsService:
    def validate_query(self, query: str) -> dict:
        """
        Check if the query is safe and on-topic.
        For demonstration, we use basic keyword rules, but in production,
        this could use a lightweight classification model.
        """
        query_lower = query.lower()
        
        # 1. Unsafe/inappropriate
        unsafe_keywords = ["hack", "kill", "bomb", "hate", "racist"]
        if any(kw in query_lower for kw in unsafe_keywords):
            return {"status": "FAIL", "reason": "UNSAFE_QUERY"}
            
        # 2. Off-topic (For this RAG system, we assume general knowledge / news is supported, 
        # but completely gibberish or out-of-bounds queries could be blocked here)
        if len(query.strip()) < 3:
            return {"status": "FAIL", "reason": "OFF_TOPIC"}
            
        return {"status": "PASS", "reason": None}

    def validate_retrieval(self, retrieved_chunks: List[dict]) -> dict:
        """
        Check if we retrieved sufficient evidence.
        """
        if not retrieved_chunks or len(retrieved_chunks) == 0:
            return {"status": "FAIL", "reason": "INSUFFICIENT_EVIDENCE"}
            
        # We could also check the top score
        top_score = max([c.get("score", 0) for c in retrieved_chunks]) if retrieved_chunks else 0
        if top_score < 0.2: # Very low similarity
            return {"status": "FAIL", "reason": "INSUFFICIENT_EVIDENCE"}
            
        return {"status": "PASS", "reason": None}

    def validate_generation(self, answer: str, grounded: bool) -> dict:
        """
        Check if the generated answer is grounded in the evidence.
        """
        if not answer or "INSUFFICIENT_EVIDENCE" in answer.upper():
            return {"status": "FAIL", "reason": "INSUFFICIENT_EVIDENCE"}
            
        if not grounded:
            return {"status": "FAIL", "reason": "UNGROUNDED_ANSWER"}
            
        return {"status": "PASS", "reason": None}

def get_guardrails_service() -> GuardrailsService:
    return GuardrailsService()
