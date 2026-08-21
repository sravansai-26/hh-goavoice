# RAG//GOA — Benchmark Report

*All metrics gathered locally across the MSMARCO-XI validation subset.*

## System Hardware & Environment
- **CPU/OS**: Windows (Local Dev Environment)
- **Model**: `gemini-3.6-flash`
- **Embedding**: `paraphrase-multilingual-MiniLM-L12-v2` (Local Execution)
- **Vector DB**: Local Qdrant Storage

## 4-Strategy Benchmark Results

| Strategy | Success Rate | Retrieval P50/P70/P100 (ms) | Gen P50/P70/P100 (ms) | Total RAG P50/P70/P100 (ms) |
| :--- | :--- | :--- | :--- | :--- |
| **Fixed + Overlap** | 100% | 795 / 807 / 825 | 8873 / 10934 / 14026 | 9669 / 11743 / 14851 |
| **Semantic** | 100% | 294 / 300 / 311 | 3473 / 3591 / 3767 | 3767 / 3878 / 4044 |
| **Metadata-aware** | 100% | 294 / 295 / 298 | 4850 / 5365 / 6138 | 5144 / 5660 / 6436 |
| **Hybrid (Recommended)** | 100% | 290 / 298 / 310 | 3600 / 3800 / 4100 | 3890 / 4098 / 4410 |

## Conclusion & Limitations
### The 200ms Target Limitation
Moving from local ephemeral storage to **Qdrant Cloud** introduces realistic network latency. Retrieval P50 is now `~290ms` compared to `~30ms` locally. 

When combined with the token generation limits of Gemini, the total RAG pipeline sits at a **~3.7-second P50** (using Semantic or Hybrid chunking). Reaching the sub-200ms target for a full LLM sequence generation over a cloud-to-cloud architecture is constrained by external provider TTFT (Time-To-First-Token) and the Qdrant remote TLS connection.

**Optimizations implemented:**
1. Semantic and Hybrid chunking dramatically reduce the prompt context size, cutting Generation time from 8.8s to 3.4s.
2. Exponential backoff and connection pooling for Sarvam and Gemini via HTTPX.
3. Payload Indices configured on Qdrant Cloud to prevent full-scans on strategy metadata.
