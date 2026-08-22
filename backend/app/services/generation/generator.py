from app.config import settings
from google import genai
from pydantic import BaseModel, Field
import time

class MultilingualAnswer(BaseModel):
    primary: str = Field(description="Answer in the user's primary language.")
    english: str = Field(description="English translation of the answer.")

class GenerationOutput(BaseModel):
    answer: MultilingualAnswer
    grounded: bool = Field(description="True if the answer is fully supported by the context, False otherwise.")
    reason: str = Field(description="If not grounded, reason why.")

class GenerationProvider:
    async def generate(self, query: str, english_query: str, context: list[dict], language_name: str) -> dict:
        raise NotImplementedError

class GeminiProvider(GenerationProvider):
    def __init__(self):
        self.api_key = settings.GENERATION_API_KEY
        self.model = "gemini-1.5-flash"
        if not self.api_key:
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)

    async def generate(self, query: str, english_query: str, context: list[dict], language_name: str) -> dict:
        import asyncio
        from google.genai import types
        
        if not self.client:
            raise Exception("GENERATION_API_KEY is not configured.")
            
        start_time = time.time()
        
        # Combine context
        context_text = "\n\n".join([f"[{i+1}] {c['text']}" for i, c in enumerate(context)])
        
        prompt = f"""
You are a highly precise, multilingual Q&A system. Your task is to answer the user's question using the provided evidence if possible.

RULES:
1. Attempt to answer from the retrieved evidence.
2. If the evidence is sufficient, set 'grounded' to true.
3. If the evidence is insufficient or irrelevant, you MUST STILL ANSWER the question using your general knowledge, BUT you MUST set 'grounded' to false.
4. Provide the 'primary' answer in the detected language: {language_name}.
5. Provide an 'english' translation of the answer in the english field. If the primary language is already English, just copy it.
6. Preserve names, numbers, dates, locations, and factual entities accurately.

Evidence:
{context_text}

Original Query ({language_name}): {query}
English Bridge Query: {english_query}
"""
        
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=GenerationOutput,
                        temperature=0.1,
                    )
                )
                
                # The response is guaranteed to match GenerationOutput schema
                import json
                result_data = json.loads(response.text)
                latency_ms = int((time.time() - start_time) * 1000)
                
                primary_ans = result_data["answer"]["primary"]
                english_ans = result_data["answer"]["english"]
                
                # The user explicitly wants to see the general knowledge answer even when ungrounded,
                # while relying on the UI to correctly display the "FAIL" guardrail state.
                # So we no longer overwrite ungrounded answers with "I don't have enough evidence..."


                return {
                    "answer_primary": primary_ans,
                    "answer_english": english_ans,
                    "grounded": result_data["grounded"],
                    "latency_ms": latency_ms
                }
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(base_delay * (2 ** attempt))
                    continue
                raise Exception(f"Generation failed after {max_retries} attempts: {str(e)}")

def get_generation_provider() -> GenerationProvider:
    return GeminiProvider()
