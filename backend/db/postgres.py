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
        cur.close()
        conn.close()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️ DB init error (continuing): {e}")
