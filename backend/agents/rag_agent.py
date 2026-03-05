from rag.retriever import retrieve
from rag.query_rewriter import rewrite_query

def rag_retriever_node(state: dict) -> dict:
    print("📚 RAG agent running...")
    queries = rewrite_query(state["topic"])
    all_results = []; seen_ids = set()
    for query in queries[:3]:
        for r in retrieve(query, top_n=3):
            if r["id"] not in seen_ids:
                seen_ids.add(r["id"]); all_results.append(r)
    return {**state, "rag_results": all_results, "queries": queries}
