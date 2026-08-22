# RAG//GOA — Voice Intelligence Lab
**Hacker House Goa 2026 — Task 02 Submission**

**Team: SyntheticMinds**
**Members:** Sravan Sai Vuppula, Sai Balaji

RAG//GOA is a production-grade, voice-enabled Retrieval-Augmented Generation (RAG) system built for the Hacker House Goa 2026. It seamlessly connects real-time voice input to a multi-strategy vector retrieval engine backed by the MSMARCO-XI dataset and Google Gemini, wrapped in a beautiful Bolt UI.

## Demo Videos
We have included two demonstration videos in the repository to showcase the system in action and our development journey:
- **[Voice RAG Demo](public/videos/voicerag-demo.mp4)**: A full demonstration of the multilingual voice-enabled RAG system in action.
- **[Build Process](public/videos/build-process.mp4)**: A walkthrough of our build process, UI design, and system architecture.

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

## Production Deployment

The system is deployed and live for Hacker House Goa 2026.

- **Frontend (Vercel)**: [https://hh-goavoice.vercel.app/](https://hh-goavoice.vercel.app/)
- **Backend (Render)**: [https://hh-goavoice.onrender.com](https://hh-goavoice.onrender.com)
- **Vector Database**: Qdrant Cloud (`msmarco_xi_chunks`)

### Architecture Notes
- The Vercel frontend communicates with the Render FastAPI backend explicitly through the `VITE_API_URL` environment variable.
- All secrets (`SARVAM_API_KEY`, `GENERATION_API_KEY`, `QDRANT_API_KEY`) remain strictly isolated in the Render backend environment variables.
- The frontend exposes absolutely zero sensitive credentials.

## Acknowledgements
Built for #RAGInGoa.
