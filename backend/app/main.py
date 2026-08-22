import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import voice, rag, performance, system

app = FastAPI(title="Voice RAG Backend", version="1.0.0")

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://hh-goavoice.vercel.app", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(voice.router, prefix="/api/voice", tags=["voice"])
app.include_router(rag.router, prefix="/api/rag", tags=["rag"])
app.include_router(performance.router, prefix="/api/performance", tags=["performance"])
app.include_router(system.router, prefix="/api/system", tags=["system"])

@app.get("/")
async def root():
    return {"message": "RAG//GOA Voice Intelligence Lab API is running"}
