import os, json
import cohere
from openai import OpenAI
from db.postgres import get_conn
from dotenv import load_dotenv
load_dotenv()

openai_client = OpenAI()
co = cohere.Client(os.environ["COHERE_API_KEY"])

def get_embedding(text: str) -> list[float]:
    return openai_client.embeddings.create(model="text-embedding-3-small", input=text).data[0].embedding

def dense_search(query: str, top_k=15) -> list[dict]:
    try:
        embedding = get_embedding(query)
        conn = get_conn(); cur = conn.cursor()
        cur.execute("""
            SELECT id, content, source, metadata,
                   1 - (embedding <=> %s::vector) AS score
            FROM documents ORDER BY score DESC LIMIT %s
        """, (embedding, top_k))
        rows = cur.fetchall(); cur.close(); conn.close()
        return [{"id": r[0], "content": r[1], "source": r[2], "metadata": r[3], "dense_score": float(r[4])} for r in rows]
    except Exception as e:
        print(f"  ⚠️ Dense search error: {e}")
        return []

def sparse_search(query: str, top_k=15) -> list[dict]:
    try:
        terms = list(set(query.lower().split()))
        conn = get_conn(); cur = conn.cursor()
        cur.execute("""
            SELECT id, content, source, metadata,
                   (SELECT COALESCE(SUM((bm25_tokens->>t)::float), 0)
                    FROM unnest(%s::text[]) t WHERE bm25_tokens ? t) AS score
            FROM documents
            ORDER BY score DESC LIMIT %s
        """, (terms, top_k))
        rows = cur.fetchall(); cur.close(); conn.close()
        return [{"id": r[0], "content": r[1], "source": r[2], "metadata": r[3], "sparse_score": float(r[4])} for r in rows]
    except Exception as e:
        print(f"  ⚠️ Sparse search error: {e}")
        return []

def rrf_merge(dense, sparse, k=60) -> list[dict]:
    scores = {}; docs_by_id = {}
    for rank, doc in enumerate(dense):
        scores[doc["id"]] = scores.get(doc["id"], 0) + 1/(k + rank + 1)
        docs_by_id[doc["id"]] = doc
    for rank, doc in enumerate(sparse):
        scores[doc["id"]] = scores.get(doc["id"], 0) + 1/(k + rank + 1)
        docs_by_id[doc["id"]] = doc
    return [docs_by_id[id_] for id_ in sorted(scores, key=scores.get, reverse=True)]

def rerank(query: str, docs: list[dict], top_n=5) -> list[dict]:
    if not docs:
        return []
    # Skip reranking if too few docs
    if len(docs) <= 2:
        return docs[:top_n]
    try:
        resp = co.rerank(
            query=query,
            documents=[d["content"] for d in docs],
            top_n=min(top_n, len(docs)),
            model="rerank-english-v3.0"
        )
        return [docs[r.index] for r in resp.results]
    except Exception as e:
        print(f"  ⚠️ Rerank error: {e} — using top-k instead")
        return docs[:top_n]

def retrieve(query: str, top_n=5) -> list[dict]:
    dense = dense_search(query)
    sparse = sparse_search(query)
    merged = rrf_merge(dense, sparse)
    return rerank(query, merged, top_n)
