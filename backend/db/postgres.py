import os
import psycopg2
from dotenv import load_dotenv
load_dotenv()

def get_db_url():
    url = os.environ.get("DATABASE_URL", "")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url

def get_conn(register=False):
    conn = psycopg2.connect(get_db_url())
    if register:
        try:
            from pgvector.psycopg2 import register_vector
            register_vector(conn)
        except Exception as e:
            print(f"⚠️ pgvector register skipped: {e}")
    return conn

def init_db():
    try:
        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.commit()
        except Exception as e:
            print(f"⚠️ vector extension skipped: {e}")
            conn.rollback()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                metadata JSONB DEFAULT '{}',
                source TEXT,
                embedding JSONB DEFAULT '[]',
                bm25_tokens JSONB DEFAULT '{}'
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️ DB init error (continuing): {e}")
