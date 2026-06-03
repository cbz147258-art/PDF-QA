from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Document, QARecord
from app.rag_engine import ask
import json

router = APIRouter(prefix="/api", tags=["qa"])

class QARequest(BaseModel):
    document_id: int
    question: str

@router.post("/ask")
async def ask_question(req: QARequest, db: AsyncSession = Depends(get_db)):
    # 查找文档
    result = await db.execute(select(Document).where(Document.id == req.document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "文档不存在")

    # RAG问答
    rag_result = await ask(req.question, doc.chroma_collection)

    # 记录到SQLite
    qa = QARecord(
        document_id=doc.id,
        question=req.question,
        answer=rag_result["answer"],
        sources=json.dumps(rag_result["sources"], ensure_ascii=False),
    )
    db.add(qa)
    await db.commit()

    return {
        "answer": rag_result["answer"],
        "sources": rag_result["sources"],
    }

@router.get("/documents")
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Document).order_by(Document.uploaded_at.desc())
    )
    docs = result.scalars().all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "chunk_count": d.chunk_count,
            "total_chars": d.total_chars,
            "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
        }
        for d in docs
    ]

@router.get("/history/{document_id}")
async def qa_history(document_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(QARecord)
        .where(QARecord.document_id == document_id)
        .order_by(QARecord.created_at.desc())
        .limit(50)
    )
    records = result.scalars().all()
    return [
        {
            "id": r.id,
            "question": r.question,
            "answer": r.answer,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]
