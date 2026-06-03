import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Document
from app.config import UPLOAD_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS
from app.pdf_processor import index_document
import aiofiles

router = APIRouter(prefix="/api", tags=["upload"])

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    # 校验扩展名
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"仅支持 {ALLOWED_EXTENSIONS} 格式")

    # 校验大小
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, f"文件不能超过 {MAX_FILE_SIZE // 1024 // 1024}MB")

    # 保存文件
    save_name = f"{uuid.uuid4().hex}_{file.filename}"
    save_path = os.path.join(UPLOAD_DIR, save_name)
    async with aiofiles.open(save_path, "wb") as f:
        await f.write(content)

    # 处理PDF并入库
    try:
        result = index_document(save_path, file.filename)
    except ValueError as e:
        os.remove(save_path)
        raise HTTPException(400, str(e))

    # 写入SQLite
    doc = Document(
        filename=file.filename,
        file_path=save_path,
        chunk_count=result["chunk_count"],
        total_chars=result["total_chars"],
        chroma_collection=result["collection_name"],
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    return {
        "id": doc.id,
        "filename": doc.filename,
        "chunk_count": doc.chunk_count,
        "message": f"上传成功，已切分为 {doc.chunk_count} 个文本块",
    }
