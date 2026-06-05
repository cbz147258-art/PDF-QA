"""
简历优化API路由 - 使用 ResumeService 专业模块
"""
import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import ResumeRecord
from app.config import UPLOAD_DIR
from app.resume_service import ResumeService
import aiofiles

router = APIRouter(prefix="/api/resume", tags=["resume"])
service = ResumeService()


async def extract_text_from_pdf(file_path: str) -> str:
    from pypdf import PdfReader
    reader = PdfReader(file_path)
    parts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            parts.append(t)
    return "\n".join(parts)


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext != ".pdf":
        raise HTTPException(400, "仅支持 PDF 格式")

    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(400, "文件不能超过 20MB")

    save_name = f"resume_{uuid.uuid4().hex}_{file.filename}"
    save_path = os.path.join(UPLOAD_DIR, save_name)
    async with aiofiles.open(save_path, "wb") as f:
        await f.write(content)

    text = await extract_text_from_pdf(save_path)
    if not text.strip():
        raise HTTPException(400, "未能从PDF中提取文本，可能是扫描版简历")

    record = ResumeRecord(
        filename=file.filename,
        file_path=save_path,
        original_text=text,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return {
        "id": record.id,
        "filename": record.filename,
        "char_count": len(text),
        "message": "简历上传成功，文本已提取",
    }


class OptimizeRequest(BaseModel):
    resume_id: int
    target: str = "general"
    position: str = ""


@router.post("/optimize")
async def optimize_resume(req: OptimizeRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ResumeRecord).where(ResumeRecord.id == req.resume_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(404, "简历不存在")

    result = await service.optimize(record.original_text, req.target, req.position)

    record.optimized_text = result["optimized"]
    record.optimize_target = req.target
    await db.commit()

    return result


class AnalyzeRequest(BaseModel):
    resume_id: int


@router.post("/analyze")
async def analyze_resume(req: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ResumeRecord).where(ResumeRecord.id == req.resume_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(404, "简历不存在")

    result = await service.analyze(record.original_text)
    return {"analysis": result["analysis"]}


@router.get("/list")
async def list_resumes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ResumeRecord).order_by(ResumeRecord.uploaded_at.desc()))
    records = result.scalars().all()
    return [{
        "id": r.id,
        "filename": r.filename,
        "char_count": len(r.original_text) if r.original_text else 0,
        "has_optimized": bool(r.optimized_text),
        "optimize_target": r.optimize_target or "",
        "uploaded_at": r.uploaded_at.isoformat() if r.uploaded_at else None,
    } for r in records]


@router.get("/{resume_id}")
async def get_resume(resume_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ResumeRecord).where(ResumeRecord.id == resume_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(404, "简历不存在")
    return {
        "id": record.id,
        "filename": record.filename,
        "original": record.original_text,
        "optimized": record.optimized_text or "",
    }


class SectionOptimizeRequest(BaseModel):
    resume_id: int
    section: str  # project, skill, summary, education
    target: str = "general"


@router.post("/optimize-section")
async def optimize_resume_section(req: SectionOptimizeRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ResumeRecord).where(ResumeRecord.id == req.resume_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(404, "简历不存在")

    optimized = await service.optimize_section(record.original_text, req.section, req.target)
    return {"optimized": optimized}
