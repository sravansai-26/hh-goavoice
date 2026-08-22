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
        self.model = settings.GENERATION_MODEL
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
You are a highly precise, multilingual Q&A system. Your task is to answer the user's question strictly based on the provided evidence.

RULES:
1. Answer ONLY from the retrieved evidence.
2. Do not invent unsupported facts.
3. If the evidence is insufficient to answer the question, output EXACTLY this string in the primary language answer: "INSUFFICIENT_EVIDENCE". Do not attempt to guess.
4. Set 'grounded' to true ONLY if you successfully answered from evidence.
5. Provide the 'primary' answer in the detected language: {language_name}.
6. Provide an 'english' translation of the answer in the english field. If the primary language is already English, just copy it.
7. Preserve names, numbers, dates, locations, and factual entities accurately.

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
                
                # Check insufficient evidence condition
                primary_ans = result_data["answer"]["primary"]
                english_ans = result_data["answer"]["english"]
                
                if "INSUFFICIENT_EVIDENCE" in primary_ans or not result_data["grounded"]:
                    if language_name.lower() == "telugu":
                        primary_ans = "ఈ ప్రశ్నకు సమాధానం ఇవ్వడానికి తగిన ఆధారాలు నాకు లభించలేదు."
                    elif language_name.lower() == "hindi":
                        primary_ans = "मुझे इस प्रश्न का उत्तर देने के लिए पर्याप्त प्रमाण नहीं मिले हैं।"
                    elif language_name.lower() == "tamil":
                        primary_ans = "இந்தக் கேள்விக்குப் பதிலளிக்க போதுமான ஆதாரங்கள் கிடைக்கவில்லை."
                    else:
                        primary_ans = "I do not have enough evidence to answer this question."
                        
                    english_ans = "I don't have enough evidence in the retrieved sources to answer this question."
                    result_data["grounded"] = False

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
