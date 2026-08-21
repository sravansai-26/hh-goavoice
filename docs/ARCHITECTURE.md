# RAG//GOA — Architecture

## 1. Full Voice-to-Answer Pipeline

```mermaid
flowchart TD
    A[Voice Input (Mic)] --> B[Frontend WAV Blob]
    B --> C[FastAPI /api/voice/transcribe]
    C --> D[Sarvam STT API]
    D --> E[Transcript Text]
    
    E --> F[FastAPI /api/rag/query]
    F --> G[Query Preprocessing & Guardrails]
    
    G --> H[Sentence Transformers Embedding]
    H --> I[(Qdrant Vector DB)]
    
    I --> J[Top-K Retrieved Context]
    J --> K[Gemini 1.5 Flash Generation]
    
    K --> L[Guardrails & Grounding Check]
    L --> M[Final Answer JSON]
    M --> N[React UI Display]
```

## 2. Ingestion & Chunking Pipeline

```mermaid
flowchart TD
    A[MSMARCO-XI Hugging Face Dataset] --> B[Data Loader (validation split)]
    B --> C{Chunking Strategy Selector}
    
    C --> D[Fixed + Overlap]
    C --> E[Semantic Boundaries]
    C --> F[Metadata-Aware]
    C --> G[Hybrid Model]
    
    D --> H[Chunk Objects]
    E --> H
    F --> H
    G --> H
    
    H --> I[Sentence Transformers Embedder]
    I --> J[Vectors + Payload]
    J --> K[(Qdrant Collection)]
```

## 3. Technology Stack
- **Frontend**: React 18, Vite, TypeScript, TailwindCSS
- **Backend**: FastAPI, Pydantic, Python 3.10+
- **Database**: Qdrant (Local memory/Cloud compatible)
- **Providers**: Sarvam (STT), Gemini (Generation)
- **Embedding**: `paraphrase-multilingual-MiniLM-L12-v2`
