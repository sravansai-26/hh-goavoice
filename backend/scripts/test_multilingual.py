import asyncio
import os
import sys
import codecs

if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.api.rag import process_rag_query, RAGRequest

async def run_tests():
    print("========================================")
    print("MULTILINGUAL VOICE-RAG PIPELINE TEST RUN")
    print("========================================")

    test_queries = [
        # 1. Telugu (Valid)
        {"lang": "te", "query": "భారత దేశం యొక్క రాజధాని ఏంటి?", "expected": "PASS"},
        # 2. Hindi (Valid)
        {"lang": "hi", "query": "भारत की राजधानी क्या है?", "expected": "PASS"},
        # 3. Tamil (Valid)
        {"lang": "ta", "query": "இந்தியாவின் தலைநகரம் என்ன?", "expected": "PASS"},
        # 4. English (Valid)
        {"lang": "en", "query": "What is the capital of India?", "expected": "PASS"},
        # 5. Off-topic (Telugu)
        {"lang": "te", "query": "నాకు ఒక జోక్ చెప్పు", "expected": "FAIL"},
        # 6. Insufficient evidence (Hindi)
        {"lang": "hi", "query": "मार्क्स का जन्म कब हुआ था?", "expected": "INSUFFICIENT"} 
    ]
    
    for i, test in enumerate(test_queries):
        print(f"\n[Test {i+1}] {test['lang'].upper()} - {test['query']}")
        req = RAGRequest(query=test["query"], language=test["lang"], strategy="hybrid", top_k=2)
        
        try:
            res = await process_rag_query(req)
            
            print(f"  English Bridge: {res.query.get('english')}")
            print(f"  Primary Answer: {res.answer.get('primary')}")
            print(f"  English Answer: {res.answer.get('english')}")
            print(f"  Grounded:       {res.grounded}")
            print(f"  Guardrail:      {res.guardrail['status']} - {res.guardrail['reason']}")
            print(f"  Total Latency:  {res.latency.get('total_ms')}ms")
            
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            
    print("\n[✔] Multilingual matrix test complete.")

if __name__ == "__main__":
    asyncio.run(run_tests())
