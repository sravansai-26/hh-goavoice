# RAG//GOA — Voice Intelligence Lab
**Hacker House Goa 2026 — Task 02 Submission**

RAG//GOA is a production-grade, voice-enabled Retrieval-Augmented Generation (RAG) system built for the Hacker House Goa 2026. It seamlessly connects real-time voice input to a multi-strategy vector retrieval engine backed by the MSMARCO-XI dataset and Google Gemini, wrapped in a beautiful Bolt UI.

## Features
- **Real Voice Capture**: Uses the browser's MediaRecorder API.
- **Voice-to-Text**: High-fidelity Indian language transcription via Sarvam API.
- **4-Strategy Vector Retrieval**: Compare Fixed+Overlap, Semantic, Metadata-aware, and Hybrid chunking strategies in real-time.
- **Grounded Generation**: Gemini 1.5 Flash generates answers strictly from retrieved evidence.
- **Robust Guardrails**: Explicitly rejects off-topic, unsafe, or ungrounded queries.
- **Extreme Latency Optimization**: Tuned for ultra-low latency with async I/O and exponential backoff.
- **Production Ready**: Fully configurable Qdrant (local/cloud) and strict error handling.

## Quickstart

### Prerequisites
- Node.js 18+
- Python 3.10+
- `uv` (optional, for fast env creation)

### Backend Setup
1. `cd backend`
2. `python -m venv venv`
3. `venv\Scripts\activate` (Windows)
4. `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and fill in your keys (Sarvam, Gemini, Qdrant).
6. Run the server: `uvicorn app.main:app --reload`

### Frontend Setup
1. `npm install`
2. `npm run dev`
3. Open `http://localhost:5173`

## Architecture & Benchmarks
- View the system design: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- View our latency numbers: [docs/BENCHMARK.md](docs/BENCHMARK.md)

## Acknowledgements
Built for #RAGInGoa.
