import os
import asyncio
from datasets import load_dataset
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.models.document import Document
from app.chunking.strategies import (
    FixedChunkingStrategy,
    SemanticChunkingStrategy,
    MetadataAwareChunkingStrategy,
    HybridChunkingStrategy
)
from app.services.embeddings.provider import get_embedding_provider
import uuid

import pandas as pd

async def main():
    print("Initializing embedding provider...")
    embedder = get_embedding_provider()
    
    print("Connecting to Qdrant...")
    from app.config import settings
    if settings.QDRANT_MODE == "cloud" and settings.clean_qdrant_url:
        client = QdrantClient(url=settings.clean_qdrant_url, api_key=settings.QDRANT_API_KEY)
    else:
        client = QdrantClient(path="local_qdrant")
    
    collection_name = "msmarco_xi_chunks"
    
    dummy_vec = await embedder.embed_query("test")
    vector_size = len(dummy_vec)
    print(f"Embedding vector size: {vector_size}")
    
    if client.collection_exists(collection_name):
        print(f"Recreating collection {collection_name} for new vector size {vector_size}...")
        client.delete_collection(collection_name=collection_name)
        
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )
    print(f"Created collection {collection_name}")

    split = os.getenv("MSMARCO_SPLIT", "validation")
    limit_str = os.getenv("MSMARCO_LIMIT", "500")
    limit = int(limit_str) if limit_str else None
    langs_str = os.getenv("MSMARCO_LANGUAGES", "hi")
    target_languages = [l.strip() for l in langs_str.split(",")]

    from datasets import load_dataset
    print(f"Loading MSMARCO-XI dataset via streaming (split={split}, limit={limit}, langs={target_languages})...")
    
    strategies = [
        FixedChunkingStrategy(chunk_size=500, overlap=80),
        SemanticChunkingStrategy(similarity_threshold=0.5),
        MetadataAwareChunkingStrategy(),
        HybridChunkingStrategy(chunk_size=500, overlap=80, similarity_threshold=0.5)
    ]
    
    batch_size = 50
    points = []
    queries_indexed = 0
    total_chunks = 0
    
    # We load streaming dataset
    try:
        ds = load_dataset("ai4bharat/MSMARCO-XI", split=split, streaming=True, trust_remote_code=True)
        # Convert to an iterator
        ds_iter = iter(ds)
        
        while queries_indexed < (limit or 500):
            try:
                row = next(ds_iter)
            except StopIteration:
                break
                
            query_id = row.get("query_id", "")
            
            # The streaming dataset for MSMARCO-XI has columns: query_id, query, query_type, passages (dict with is_selected, url, translated_passages)
            passages_data = row.get("passages", {})
            
            if isinstance(passages_data, dict):
                # The actual fields might be different. Let's try to extract passages.
                passages = passages_data.get("Translated_passages", passages_data.get("passage_text", []))
                is_selected = passages_data.get("is_selected", [])
            else:
                passages = []
                is_selected = []
                
            # If empty, skip
            if not passages:
                continue
                
            # We will assume lang is 'hi' for this row if not specified
            lang = "hi"
            
            for p_idx, text in enumerate(passages):
                if not text or not str(text).strip():
                    continue
                    
                doc = Document(
                    document_id=f"{query_id}_{p_idx}",
                    text=str(text),
                    language=lang,
                    metadata={
                        "query_id": query_id,
                        "query_type": row.get("query_type", ""),
                        "is_selected": bool(is_selected[p_idx]) if p_idx < len(is_selected) else False,
                        "query_text": row.get("query", "")
                    }
                )
                
                # Chunk with all strategies to ensure fair comparison
                for strategy in strategies:
                    chunks = await strategy.chunk(doc)
                    for chunk in chunks:
                        vec = await embedder.embed_query(chunk.text)
                        points.append(
                            PointStruct(
                                id=str(uuid.uuid4()),
                                vector=vec,
                                payload=chunk.model_dump()
                            )
                        )
                        total_chunks += 1
                        
                        if len(points) >= batch_size:
                            client.upsert(collection_name=collection_name, points=points)
                            print(f"Upserted {len(points)} chunks... (Total: {total_chunks})")
                            points = []
                            
            queries_indexed += 1
            if queries_indexed % 10 == 0:
                print(f"Processed {queries_indexed} queries...")
                
    except Exception as e:
        print(f"Dataset streaming failed: {e}")
        
    if points:
        client.upsert(collection_name=collection_name, points=points)
        print(f"Upserted {len(points)} chunks... (Total: {total_chunks})")
        
    print(f"\nIngestion complete!")
    print(f"Config: split={split}, languages={target_languages}, records_indexed={queries_indexed}")
    print(f"Total chunks indexed: {total_chunks}")
    print(f"Vector Collection: {collection_name}")
    print(f"Strategies generated: Fixed, Semantic, Metadata, Hybrid")

if __name__ == "__main__":
    asyncio.run(main())
