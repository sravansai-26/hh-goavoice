import asyncio
from qdrant_client import QdrantClient

async def main():
    client = QdrantClient(path="local_qdrant")
    res = client.scroll(
        collection_name="msmarco_xi_chunks",
        limit=2,
        with_payload=True
    )
    for p in res[0]:
        print(f"Query: {p.payload.get('metadata', {}).get('query_text')}")
        print(f"Text: {p.payload.get('text')}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
