from app.config import settings
from google import genai
import time

class GenerationProvider:
    async def generate(self, query: str, context: list[dict], language: str) -> dict:
        raise NotImplementedError

class GeminiProvider(GenerationProvider):
    def __init__(self):
        self.api_key = settings.GENERATION_API_KEY
        self.model = settings.GENERATION_MODEL
        if not self.api_key:
            # Fallback mock for local testing
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)

    async def generate(self, query: str, context: list[dict], language: str) -> dict:
        import asyncio
        
        if not self.client:
            raise Exception("GENERATION_API_KEY is not configured.")
            
        start_time = time.time()
        
        # Combine context
        context_text = "\n\n".join([f"[{i+1}] {c['text']}" for i, c in enumerate(context)])
        
        prompt = f"""
You are an expert Q&A system. Your task is to answer the user's question based strictly on the provided context.
Follow these rules:
1. Answer ONLY from the retrieved evidence.
2. Do not invent unsupported facts.
3. If the evidence is insufficient to answer the question, output EXACTLY: "INSUFFICIENT_EVIDENCE".
4. Maintain the requested language: {language}.
5. Use citations in brackets like [1] to refer to the context.

Context:
{context_text}

Question: {query}
Answer:
"""
        
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                # Use async client
                response = await self.client.aio.models.generate_content(
                    model=self.model,
                    contents=prompt,
                )
                answer = response.text.strip()
                
                latency_ms = int((time.time() - start_time) * 1000)
                
                if answer == "INSUFFICIENT_EVIDENCE":
                    return {
                        "answer": "",
                        "citations": [],
                        "grounded": False,
                        "reason": "INSUFFICIENT_EVIDENCE",
                        "latency_ms": latency_ms
                    }
                    
                return {
                    "answer": answer,
                    "citations": [], # Ideally parse citations from text
                    "grounded": True,
                    "latency_ms": latency_ms
                }
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(base_delay * (2 ** attempt))
                    continue
                raise Exception(f"Generation failed after {max_retries} attempts: {str(e)}")

def get_generation_provider() -> GenerationProvider:
    if settings.GENERATION_PROVIDER == "gemini":
        return GeminiProvider()
    # Add OpenAI/Anthropic fallback here later if needed
    return GeminiProvider()
