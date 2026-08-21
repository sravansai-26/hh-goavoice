import asyncio
import time
import numpy as np
from rich.console import Console
from rich.table import Table

import httpx

async def run_benchmark():
    console = Console()
    console.print("[bold cyan]Starting RAG Benchmarking Engine (API Mode)[/bold cyan]")
    
    # Representative benchmark query set
    queries = [
        "भारत की राजधानी क्या है?",
        "ताजमहल किसने बनवाया था?"
    ]
    
    strategies = ["fixed", "semantic", "metadata", "hybrid"]
    
    results = {s: {"retrieval": [], "generation": [], "total": [], "success": 0} for s in strategies}
    
    console.print(f"Running benchmark across {len(queries)} queries and {len(strategies)} strategies...\n")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for strategy in strategies:
            console.print(f"Evaluating Strategy: [bold yellow]{strategy}[/bold yellow]")
            for query in queries:
                try:
                    res = await client.post(
                        "http://127.0.0.1:8001/api/rag/query",
                        json={"query": query, "strategy": strategy}
                    )
                    
                    if res.status_code != 200:
                        console.print(f"[red]API Error: {res.status_code} - {res.text}[/red]")
                        results[strategy]["retrieval"].append(0)
                        results[strategy]["generation"].append(0)
                        results[strategy]["total"].append(0)
                        continue
                        
                    data = res.json()
                    
                    latency = data.get("latency", {})
                    retrieval_ms = latency.get("retrieval_ms", 0)
                    gen_ms = latency.get("generation_ms", 0)
                    total_ms = latency.get("total_ms", 0)
                    success = 1 if data.get("guardrail", {}).get("final_status") == "PASS" or data.get("guardrail", {}).get("status") == "PASS" else 0
                    
                    if success == 0:
                        console.print(f"[yellow]Failed Guardrail: {data.get('guardrail')}[/yellow]")
                    
                    results[strategy]["retrieval"].append(retrieval_ms)
                    results[strategy]["generation"].append(gen_ms)
                    results[strategy]["total"].append(total_ms)
                    results[strategy]["success"] += success
                    
                except Exception as e:
                    console.print(f"[red]Error during query: {repr(e)}[/red]")
                    results[strategy]["retrieval"].append(0)
                    results[strategy]["generation"].append(0)
                    results[strategy]["total"].append(0)
                    
                # Add delay to avoid hitting Gemini Free Tier 5 RPM rate limit
                await asyncio.sleep(12)

            
    # Generate Report Table
    table = Table(title="Chunking Strategies Benchmark Report", show_header=True, header_style="bold magenta")
    table.add_column("Strategy")
    table.add_column("Success Rate")
    table.add_column("Ret P50/P70/P100 (ms)")
    table.add_column("Gen P50/P70/P100 (ms)")
    table.add_column("Total P50/P70/P100 (ms)")
    
    for strategy in strategies:
        r = results[strategy]
        ret = np.array(r["retrieval"]) if r["retrieval"] else np.array([0])
        gen = np.array(r["generation"]) if r["generation"] else np.array([0])
        tot = np.array(r["total"]) if r["total"] else np.array([0])
        
        success_rate = f"{(r['success'] / len(queries)) * 100:.0f}%"
        
        def p_str(arr):
            return f"{np.percentile(arr, 50):.0f}/{np.percentile(arr, 70):.0f}/{np.percentile(arr, 100):.0f}"
            
        table.add_row(
            strategy,
            success_rate,
            p_str(ret),
            p_str(gen),
            p_str(tot)
        )
        
    console.print(table)

if __name__ == "__main__":
    asyncio.run(run_benchmark())
