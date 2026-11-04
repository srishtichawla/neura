import os
import psycopg2
from dotenv import load_dotenv
load_dotenv()

EMBEDDING_DIM = 1536  # text-embedding-3-small


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

        # FIX: embedding must be a real pgvector column, otherwise the
        # `<=>` operator used by the retriever fails (jsonb <=> vector).
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                metadata JSONB DEFAULT '{{}}',
                source TEXT,
                embedding vector({EMBEDDING_DIM}),
                bm25_tokens JSONB DEFAULT '{{}}'
            );
        """)
        conn.commit()

        # Migrate databases created with the old jsonb embedding column.
        cur.execute("""
            SELECT data_type FROM information_schema.columns
            WHERE table_name = 'documents' AND column_name = 'embedding'
        """)
        row = cur.fetchone()
        if row and row[0] == "jsonb":
            print("🔧 Migrating documents.embedding from jsonb to vector...")
            cur.execute("ALTER TABLE documents ALTER COLUMN embedding DROP DEFAULT;")
            cur.execute(f"""
                ALTER TABLE documents
                ALTER COLUMN embedding TYPE vector({EMBEDDING_DIM})
                USING CASE
                    WHEN jsonb_typeof(embedding) = 'array'
                         AND jsonb_array_length(embedding) = {EMBEDDING_DIM}
                    THEN embedding::text::vector
                    ELSE NULL
                END;
            """)
            conn.commit()
            print("✅ Migration done")

        cur.execute("CREATE INDEX IF NOT EXISTS documents_source_idx ON documents (source);")
        conn.commit()

        # ---- Accounts, per-user documents, saved reports ----
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                topic TEXT NOT NULL,
                report TEXT NOT NULL,
                citations JSONB NOT NULL DEFAULT '[]',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS reports_user_idx ON reports (user_id, created_at DESC);")
        # Each document chunk belongs to a user (older rows stay NULL = nobody's)
        cur.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;")
        cur.execute("CREATE INDEX IF NOT EXISTS documents_user_idx ON documents (user_id);")
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️ DB init error (continuing): {e}")