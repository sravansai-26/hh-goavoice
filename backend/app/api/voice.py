from fastapi import APIRouter, UploadFile, File, HTTPException
import time
from app.services.stt.sarvam import SarvamSTTProvider
from pydantic import BaseModel

router = APIRouter()
stt_provider = SarvamSTTProvider()

class VoiceTranscribeResponse(BaseModel):
    success: bool
    transcript: str
    language: str
    duration_ms: int
    error: dict = None

from app.services.translation import translator

@router.post("/transcribe", response_model=VoiceTranscribeResponse)
async def transcribe_voice(file: UploadFile = File(...)):
    start_time = time.time()
    
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
        
    audio_bytes = await file.read()
    if len(audio_bytes) == 0:
        return VoiceTranscribeResponse(
            success=False, transcript="", language="", duration_ms=0,
            error={"code": "EMPTY_AUDIO", "message": "Audio file is empty"}
        )
        
    try:
        # Using filename to pass extension to the STT provider if needed
        result = await stt_provider.transcribe(audio_bytes, filename=file.filename)
        
        # Translate to english concurrently so the frontend has it immediately
        transcript = result["transcript"]
        lang_code = result["language_code"]
        
        if lang_code == "en":
            english_transcript = transcript
        else:
            trans_res = await translator.translate_to_english(transcript)
            english_transcript = trans_res.get("english_query", transcript)
            
        duration_ms = int((time.time() - start_time) * 1000)
        
        return VoiceTranscribeResponse(
            success=True,
            transcript=transcript,
            language=lang_code,
            duration_ms=duration_ms,
            error={"english_transcript": english_transcript} # Hack to pass it without changing Pydantic schema in 1 file
        )
    except Exception as e:
        return VoiceTranscribeResponse(
            success=False, transcript="", language="", duration_ms=0,
            error={"code": "STT_FAILED", "message": str(e)}
        )
