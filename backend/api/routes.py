import json
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from graph.orchestrator import build_graph
from rag.ingest import ingest_text

router = APIRouter()
uploaded_docs = []  # in-memory store of uploaded files

class ResearchRequest(BaseModel):
    topic: str

@router.post("/research/stream")
async def stream_research(req: ResearchRequest):
    graph = build_graph()
    async def event_stream():
        try:
            async for event in graph.astream({"topic": req.topic}):
                node_name = list(event.keys())[0]
                yield f"data: {json.dumps({'node': node_name, 'state': event})}\n\n"
            yield f"data: {json.dumps({'node': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'node': 'error', 'message': str(e)})}\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@router.post("/research")
async def run_research(req: ResearchRequest):
    graph = build_graph()
    result = await graph.ainvoke({"topic": req.topic})
    return {"report": result.get("final_report",""), "citations": result.get("citations",[])}

@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    content = await file.read()
    filename = file.filename or "upload"
    size_mb = round(len(content) / (1024 * 1024), 2)

    if filename.lower().endswith(".pdf"):
        try:
            import fitz
            doc = fitz.open(stream=content, filetype="pdf")
            total_pages = len(doc)
            text = ""
            for i in range(total_pages):  # process ALL pages
                text += doc[i].get_text()
            doc.close()
            if not text.strip():
                raise HTTPException(400, "PDF has no extractable text (scanned/image-based PDF)")
        except ImportError:
            raise HTTPException(500, "pymupdf not installed — run: pip install pymupdf")
    else:
        try:
            text = content.decode("utf-8")
        except:
            raise HTTPException(400, "File must be UTF-8 text or PDF")
        total_pages = None

    count = ingest_text(text, source=filename)

    doc_info = {
        "filename": filename,
        "size_mb": size_mb,
        "chunks": count,
        "pages": total_pages,
    }
    uploaded_docs.append(doc_info)

    return {
        "status": "success",
        "chunks_ingested": count,
        "filename": filename,
        "size_mb": size_mb,
        "pages": total_pages,
    }

@router.get("/documents")
async def list_documents():
    return {"documents": uploaded_docs}

@router.get("/health")
async def health():
    return {"status": "ok"}
