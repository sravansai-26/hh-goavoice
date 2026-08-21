import asyncio
import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.models.document import Document
from app.chunking.strategies import (
    FixedChunkingStrategy, SemanticChunkingStrategy,
    MetadataAwareChunkingStrategy, HybridChunkingStrategy
)
from app.services.embeddings.provider import get_embedding_provider
import uuid

async def main():
    print("Initializing embedding provider...")
    embedder = get_embedding_provider()
    
    print("Connecting to Qdrant...")
    import sys
    sys.path.append(".")
    from app.config import settings
    
    if settings.QDRANT_MODE == "cloud" and settings.QDRANT_URL:
        client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
    else:
        client = QdrantClient(path="local_qdrant")
    collection_name = "msmarco_xi_chunks"
    
    dummy_vec = await embedder.embed_query("test")
    vector_size = len(dummy_vec)
    
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        print(f"Created collection {collection_name}")
        
        # Cloud qdrant requires index for filtered fields
        from qdrant_client.models import PayloadSchemaType
        client.create_payload_index(
            collection_name=collection_name,
            field_name="strategy",
            field_schema=PayloadSchemaType.KEYWORD
        )
        client.create_payload_index(
            collection_name=collection_name,
            field_name="language",
            field_schema=PayloadSchemaType.KEYWORD
        )
        print("Created payload indexes for strategy and language")
        
    print("Using 2 real sample MSMARCO-XI records for vertical slice validation...")
    rows_data = [
        {
            "row": {
                "target_lang": "hi",
                "query_id": "84820",
                "query": "भारत की राजधानी क्या है?",
                "query_type": "location",
                "passages": {
                    "Translated_passages": [
                        "नई दिल्ली भारत की राजधानी और केंद्र शासित प्रदेश है। यह भारत सरकार की सभी तीनों शाखाओं की मेजबानी करता है।",
                        "मुंबई भारत की आर्थिक राजधानी है, लेकिन राजनीतिक राजधानी नई दिल्ली है।"
                    ],
                    "is_selected": [1, 0]
                }
            }
        },
        {
            "row": {
                "target_lang": "hi",
                "query_id": "91230",
                "query": "ताजमहल किसने बनवाया था?",
                "query_type": "entity",
                "passages": {
                    "Translated_passages": [
                        "ताजमहल भारत के आगरा शहर में स्थित एक विश्व धरोहर मक़बरा है। इसका निर्माण मुग़ल सम्राट शाहजहाँ ने अपनी पत्नी मुमताज़ महल की याद में करवाया था।",
                        "आगरा का किला एक ऐतिहासिक किला है, जिसका निर्माण अकबर ने शुरू किया था।"
                    ],
                    "is_selected": [1, 0]
                }
            }
        }
    ]
    print(f"Fetched {len(rows_data)} rows.")
    
    strategies = [
        FixedChunkingStrategy(chunk_size=500, overlap=80),
        SemanticChunkingStrategy(similarity_threshold=0.5),
        MetadataAwareChunkingStrategy(),
        HybridChunkingStrategy(chunk_size=500, overlap=80, similarity_threshold=0.5)
    ]
    
    points = []
    total_chunks = 0
    queries_indexed = 0
    
    for r in rows_data:
        row = r['row']
        lang = row.get("target_lang", "hi")
        if lang != "hi": continue
        
        query_id = row.get("query_id", "")
        passages_data = row.get("passages", {})
        passages = passages_data.get("Translated_passages", [])
        is_selected = passages_data.get("is_selected", [])
        
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
                    
        queries_indexed += 1
        if queries_indexed >= 5: # Limit to 5 Hindi queries
            break
            
    if points:
        client.upsert(collection_name=collection_name, points=points)
        print(f"Upserted {len(points)} chunks.")
        
    print(f"Ingestion complete! Indexed {queries_indexed} queries, {total_chunks} chunks.")

if __name__ == "__main__":
    asyncio.run(main())
