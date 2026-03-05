import os, psycopg2
from dotenv import load_dotenv
load_dotenv()

def get_conn(register=True):
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    if register:
        from pgvector.psycopg2 import register_vector
        register_vector(conn)
    return conn

def init_db():
    # First connect WITHOUT registering vector (extension doesn't exist yet)
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    conn.commit()
    cur.close()
    conn.close()

    # Now connect WITH vector registered
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
    cur.execute("CREATE INDEX IF NOT EXISTS docs_embedding_idx ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);")
    conn.commit(); cur.close(); conn.close()
    print("✅ Database initialized")

if __name__ == "__main__":
    init_db()
