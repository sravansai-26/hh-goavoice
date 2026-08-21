import os
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

def main():
    print("VECTOR INDEX VERIFICATION\n")
    try:
        import sys
        sys.path.append(".")
        from app.config import settings
        
        if settings.QDRANT_MODE == "cloud" and settings.QDRANT_URL:
            client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
        else:
            client = QdrantClient(path="local_qdrant")
            
        collection_name = "msmarco_xi_chunks"
        
        if not client.collection_exists(collection_name):
            print(f"Collection {collection_name} does not exist.")
            return
            
        print(f"Collection: {collection_name}")
        print("Status: READY")
        
        collection_info = client.get_collection(collection_name)
        print(f"\nVectors: {collection_info.points_count}")
        
        # Dimensions and metric
        config = collection_info.config.params.vectors
        print(f"Dimension: {config.size}")
        print(f"Distance: {config.distance.name}")
        
        # We can try to fetch a sample to see languages and strategies
        points, _ = client.scroll(
            collection_name=collection_name,
            limit=100,
            with_payload=True
        )
        
        languages = set()
        strategies = set()
        for p in points:
            if p.payload:
                lang = p.payload.get("language")
                if lang: languages.add(lang)
                strat = p.payload.get("strategy")
                if strat: strategies.add(strat)
                
        print(f"\nLanguages: {', '.join(languages)}")
        print(f"Strategies present: {', '.join(strategies)}")
        
        print("\nSample search:")
        # Dummy search
        dummy_vector = [0.0] * config.size
        search_res = client.search(
            collection_name=collection_name,
            query_vector=dummy_vector,
            limit=1
        )
        if search_res:
            print("PASS")
        else:
            print("FAIL (No results returned)")
            
    except Exception as e:
        print(f"Status: ERROR\n{e}")

if __name__ == "__main__":
    main()
