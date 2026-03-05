import os, json
from openai import OpenAI
from db.postgres import get_conn
from dotenv import load_dotenv
load_dotenv()

client = OpenAI()

def chunk_text(text: str, chunk_size=500, overlap=50) -> list[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk: chunks.append(chunk)
    return chunks

def get_embedding(text: str) -> list[float]:
    return client.embeddings.create(model="text-embedding-3-small", input=text).data[0].embedding

def compute_bm25_tokens(text: str) -> dict:
    tokens = text.lower().split()
    freq = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1
    return freq

def ingest_text(text: str, source: str = "manual", metadata: dict = {}):
    chunks = chunk_text(text)
    conn = get_conn(); cur = conn.cursor()
    for chunk in chunks:
        embedding = get_embedding(chunk)
        bm25_tokens = compute_bm25_tokens(chunk)
        cur.execute("""
            INSERT INTO documents (content, metadata, source, embedding, bm25_tokens)
            VALUES (%s, %s, %s, %s, %s)
        """, (chunk, json.dumps(metadata), source, embedding, json.dumps(bm25_tokens)))
    conn.commit(); cur.close(); conn.close()
    print(f"✅ Ingested {len(chunks)} chunks from '{source}'")
    return len(chunks)
