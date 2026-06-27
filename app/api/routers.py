import asyncio
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from app.rag.chain import build_rag_chain
from app.rag.chunker import split_documents
from app.rag.loader import load_pdf_bytes
from app.rag.vectorstore import build_vectorstore, get_retriever
from app.config import RETRIEVER_K, has_groq_api_key
from app.api.models import QueryRequest, QueryResponse, IngestResponse

router = APIRouter()
QUERY_TIMEOUT_SECONDS = 90

_vectorstore = None
_retriever = None
_rag_chain = None

@router.get("/health")
async def health():
    api_key_configured = has_groq_api_key()
    return {
        "status": "ok",
        "document_loaded": _rag_chain is not None,
        "api_key_configured": api_key_configured,
    }


@router.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    global _vectorstore, _retriever, _rag_chain

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )
    
    data = await file.read()

    try:
        documents = load_pdf_bytes(data, file.filename)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read PDF: {e}"
        ) from e
    
    if not documents:
        raise HTTPException(
            status_code=400,
            detail="The PDF did not contain any readable pages."
        )
    
    chunks = await run_in_threadpool(split_documents, documents)
    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="The PDF did not contain any extractable text."
        )
    
    use_groq = has_groq_api_key()
    try:
        if use_groq:
            vectorstore = await run_in_threadpool(build_vectorstore, chunks)
            retriever = get_retriever()
            rag_chain = build_rag_chain(retriever)
    except Exception as e:
        raise HTTPException(
            status_code=502, 
            detail=f"Could not initialize RAG pipeline."
        ) from e
    
    _vectorstore = vectorstore
    _retriever = retriever
    _rag_chain = rag_chain

    return IngestResponse(
        message=f"'{file.filename}' ingested successfully.",
        pages=len(documents),
        chunks=len(chunks),
    )


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    if _rag_chain is None:
        raise HTTPException(
            status_code=400,
            detail="No document loaded. POST a PDF to /api/ingest first."
        )
    
    try:
        answer = await asyncio.wait_for(
            run_in_threadpool(_rag_chain.invoke, req.question),
            timeout=QUERY_TIMEOUT_SECONDS
        )
    except Exception as e:
        raise HTTPException(
            status_code=504,
            detail="The model request timed out. Try again, or use a shorter question."
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Could not generate an answer: {e}",
        ) from e
    
    source_docs = await run_in_threadpool(_retriever.invoke, req.question)
    sources = []
    seen = set()
    for doc in source_docs[:RETRIEVER_K]:
        page = doc.metadata.get("page")
        page_label = f"p.{page + 1}" if isinstance(page, int) else "page unknown"
        source = f"{doc.metadata.get('source', 'unknown')} — {page_label}"
        if source not in seen:
            sources.append(source)
            seen.add(source)

    return QueryResponse(answer=answer, sources=sources)