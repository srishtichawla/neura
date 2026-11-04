import json
import openai
import psycopg2
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from graph.orchestrator import build_graph
from rag.ingest import ingest_text
from auth import current_user
from db.postgres import get_conn

router = APIRouter()

class ResearchRequest(BaseModel):
    topic: str

@router.post("/research/stream")
async def stream_research(req: ResearchRequest, user: dict = Depends(current_user)):
    graph = build_graph()
    async def event_stream():
        try:
            async for event in graph.astream({"topic": req.topic, "user_id": user["id"]}):
                node_name = list(event.keys())[0]
                yield f"data: {json.dumps({'node': node_name, 'state': event})}\n\n"
            yield f"data: {json.dumps({'node': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'node': 'error', 'message': str(e)})}\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@router.post("/research")
async def run_research(req: ResearchRequest, user: dict = Depends(current_user)):
    graph = build_graph()
    result = await graph.ainvoke({"topic": req.topic, "user_id": user["id"]})
    return {"report": result.get("final_report",""), "citations": result.get("citations",[])}

MAX_UPLOAD_MB = 25
ALLOWED_EXTENSIONS = (".pdf", ".txt", ".md", ".csv")


def _extract_text(content: bytes, filename: str):
    """Blocking text extraction. Returns (text, total_pages)."""
    if filename.lower().endswith(".pdf"):
        try:
            import fitz  # pymupdf
        except ImportError:
            raise HTTPException(500, "pymupdf not installed — run: pip install pymupdf")
        try:
            doc = fitz.open(stream=content, filetype="pdf")
        except Exception:
            raise HTTPException(400, "Could not open this PDF (corrupt or password-protected)")
        try:
            if doc.needs_pass:
                raise HTTPException(400, "This PDF is password-protected")
            total_pages = len(doc)
            text = "\n".join(page.get_text() for page in doc)
        finally:
            doc.close()
        if not text.strip():
            raise HTTPException(400, "PDF has no extractable text (scanned/image-based PDF)")
        return text, total_pages

    for enc in ("utf-8-sig", "utf-16", "latin-1"):
        try:
            return content.decode(enc), None
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise HTTPException(400, "File must be UTF-8 text or PDF")


def _process_upload(content: bytes, filename: str, user_id: int, size_mb: float):
    """Blocking: extract text + embed + store. Runs in a worker thread."""
    text, total_pages = _extract_text(content, filename)
    count = ingest_text(text, source=filename, user_id=user_id,
                        metadata={"size_mb": size_mb, "pages": total_pages})
    if count == 0:
        raise HTTPException(400, "No text found in the file")
    return count, total_pages


@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...), user: dict = Depends(current_user)):
    filename = file.filename or "upload"
    if not filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(400, f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    content = await file.read()
    size_mb = round(len(content) / (1024 * 1024), 2)
    if not content:
        raise HTTPException(400, "The uploaded file is empty")
    if size_mb > MAX_UPLOAD_MB:
        raise HTTPException(413, f"File too large ({size_mb} MB). Max is {MAX_UPLOAD_MB} MB")

    try:
        # Run blocking work (PDF parsing, OpenAI calls, DB writes) off the event loop
        count, total_pages = await run_in_threadpool(_process_upload, content, filename, user["id"], size_mb)
    except HTTPException:
        raise
    except openai.AuthenticationError:
        raise HTTPException(500, "OpenAI API key is invalid or missing on the server")
    except openai.RateLimitError:
        raise HTTPException(429, "OpenAI rate limit/quota reached — try again shortly")
    except openai.APIConnectionError:
        raise HTTPException(502, "Could not reach OpenAI — try again")
    except psycopg2.Error as e:
        print(f"❌ Database error during ingest: {e}")
        raise HTTPException(500, "Database error while saving the document")
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(500, f"Ingest failed: {type(e).__name__}: {e}")

    return {
        "status": "success",
        "chunks_ingested": count,
        "filename": filename,
        "size_mb": size_mb,
        "pages": total_pages,
    }

@router.get("/documents")
async def list_documents(user: dict = Depends(current_user)):
    def _q():
        conn = get_conn()
        try:
            cur = conn.cursor()
            cur.execute("""SELECT source, COUNT(*), (array_agg(metadata ORDER BY id))[1]
                           FROM documents WHERE user_id = %s
                           GROUP BY source ORDER BY MIN(id)""", (user["id"],))
            out = []
            for source, chunks, meta in cur.fetchall():
                meta = meta or {}
                out.append({"filename": source, "chunks": chunks,
                            "size_mb": meta.get("size_mb", 0), "pages": meta.get("pages")})
            return out
        finally:
            conn.close()
    return {"documents": await run_in_threadpool(_q)}

@router.get("/health")
async def health():
    return {"status": "ok"}