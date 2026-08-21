import httpx
from app.config import settings

class SarvamSTTProvider:
    def __init__(self):
        self.api_key = settings.SARVAM_API_KEY
        self.url = "https://api.sarvam.ai/speech-to-text"
        
    async def transcribe(self, audio_bytes: bytes, filename: str = "audio.wav") -> dict:
        import asyncio
        import logging
        
        if not self.api_key:
            raise Exception("SARVAM_API_KEY is not configured.")
            
        headers = {
            "api-subscription-key": self.api_key
        }
        
        files = {
            "file": (filename, audio_bytes, "audio/wav")
        }
        data = {
            "model": "saaras:v3",
            "mode": "transcribe"
        }
        
        max_retries = 3
        base_delay = 1.0
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt in range(max_retries):
                try:
                    response = await client.post(self.url, headers=headers, files=files, data=data)
                    
                    if response.status_code == 200:
                        result = response.json()
                        return {
                            "transcript": result.get("transcript", ""),
                            "language_code": result.get("language_code", "hi")
                        }
                    elif response.status_code in [400, 401, 403, 404]:
                        # Permanent errors
                        raise Exception(f"Permanent Sarvam API error {response.status_code}: {response.text}")
                    else:
                        # Transient errors
                        if attempt < max_retries - 1:
                            await asyncio.sleep(base_delay * (2 ** attempt))
                            continue
                        raise Exception(f"Transient Sarvam API error {response.status_code}: {response.text}")
                
                except httpx.RequestError as e:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(base_delay * (2 ** attempt))
                        continue
                    raise Exception(f"Sarvam connection error: {str(e)}")
