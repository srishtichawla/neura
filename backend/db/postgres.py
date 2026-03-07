import os
import psycopg2
from dotenv import load_dotenv
load_dotenv()

def get_db_url():
    url = os.environ["DATABASE_URL"]
    # Railway uses postgres:// but psycopg2 needs postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url

def get_conn(register=True):
    conn = psycopg2.connect(get_db_url())
    if register:
        from pgvector.psycopg2 import register_vector
        register_vector(conn)
    return conn

def init_db():
    conn = psycopg2.connect(get_db_url())
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    conn.commit()
    cur.close()
    conn.close()

    conn = get_conn(register=True)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            metadata JSONB DEFAULT '{}',
            source TEXT,
            embedding vector(1536),
            bm25_tokens JSONB DEFAULT '{}'
        );
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS docs_embedding_idx
        ON documents USING hnsw (embedding vector_cosine_ops);
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Database initialized")
