import json
from openai import OpenAI
from psycopg2.extras import execute_values
from db.postgres import get_conn
from dotenv import load_dotenv
load_dotenv()

client = OpenAI()

EMBED_MODEL = "text-embedding-3-small"
EMBED_BATCH_SIZE = 64   # chunks per OpenAI request (API allows up to 2048)
INSERT_PAGE_SIZE = 100


def clean_text(text: str) -> str:
    """Postgres rejects NUL (0x00) bytes, which PDFs often contain."""
    return text.replace("\x00", "").strip()


def chunk_text(text: str, chunk_size=500, overlap=50) -> list[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks


def get_embedding(text: str) -> list[float]:
    return client.embeddings.create(model=EMBED_MODEL, input=text).data[0].embedding


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Embed many chunks with one API call per batch (huge speed-up)."""
    out: list[list[float]] = []
    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i:i + EMBED_BATCH_SIZE]
        resp = client.embeddings.create(model=EMBED_MODEL, input=batch)
        # API returns items with .index; sort to be safe
        out.extend(d.embedding for d in sorted(resp.data, key=lambda d: d.index))
    return out


def compute_bm25_tokens(text: str) -> dict:
    tokens = text.lower().split()
    freq = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1
    return freq


def ingest_text(text: str, source: str = "manual", metadata: dict | None = None) -> int:
    metadata = metadata or {}
    text = clean_text(text)
    source = clean_text(source) or "upload"
    chunks = chunk_text(text)
    if not chunks:
        return 0

    # Embed first (network) so we don't hold a DB connection while waiting
    embeddings = get_embeddings(chunks)

    rows = [
        (
            chunk,
            json.dumps(metadata),
            source,
            "[" + ",".join(map(str, emb)) + "]",   # pgvector text format
            json.dumps(compute_bm25_tokens(chunk)),
        )
        for chunk, emb in zip(chunks, embeddings)
    ]

    conn = get_conn()
    try:
        cur = conn.cursor()
        execute_values(
            cur,
            "INSERT INTO documents (content, metadata, source, embedding, bm25_tokens) VALUES %s",
            rows,
            template="(%s, %s::jsonb, %s, %s::vector, %s::jsonb)",
            page_size=INSERT_PAGE_SIZE,
        )
        conn.commit()
        cur.close()
    except Exception:
        conn.rollback()  # all-or-nothing: no half-ingested documents
        raise
    finally:
        conn.close()

    print(f"✅ Ingested {len(chunks)} chunks from '{source}'")
    return len(chunks)
