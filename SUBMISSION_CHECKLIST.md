# Hacker House Goa 2026 — Task 02 Submission Checklist

## Required Components
- [x] **Real voice input**: Browser MediaRecorder API used (no typed fallback).
- [x] **Voice-to-text transcription**: Sarvam STT integrated (`saaras:v3`).
- [x] **Chunking Strategies**:
  - [x] Fixed + Overlap
  - [x] Semantic
  - [x] Metadata-aware
  - [x] Hybrid
- [x] **Vector retrieval**: Qdrant Vector Search over MSMARCO-XI chunks.
- [x] **Grounded generation**: Gemini Flash 1.5 strictly uses retrieved context.
- [x] **Orchestration harness**: FastAPI backend with Pydantic I/O.
- [x] **Retries and structured I/O**: Implemented in Python API routes.
- [x] **Guardrails**: Explicit rejection for off-topic, ungrounded, or unsafe prompts.
- [x] **Latency Benchmarking**: Completed (see `docs/BENCHMARK.md`).

## Verification
- [x] **Code Quality**: All TS errors resolved, React UI completely functional.
- [x] **Secret Scan**: No `.env`, `telemetry.db`, `local_qdrant` committed.
- [x] **Production Config**: `QDRANT_MODE=cloud` fallback ready.
- [x] **Documentation**: `README.md`, `ARCHITECTURE.md`, `BENCHMARK.md` written.

## Final Submission Steps (For User)
1. Push to GitHub (`git push origin main`).
2. Deploy backend (e.g., Render, Railway) setting required `.env` variables.
3. Deploy frontend (e.g., Vercel, Netlify) connecting `VITE_API_URL` to backend.
4. Record Demo Video showcasing Voice -> Answer on a mobile device.
5. Post on social media with `#RAGInGoa`.
