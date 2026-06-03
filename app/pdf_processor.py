import os
import hashlib
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from fastembed import TextEmbedding
import chromadb
from app.config import (
    CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL_NAME,
    CHROMA_PERSIST_DIR, TOP_K_RETRIEVAL
)

# fastembed: 轻量级，无需 PyTorch，首次运行自动下载模型（约400MB）
embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL_NAME)

chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

def extract_text(file_path: str) -> str:
    """从PDF中提取纯文本"""
    reader = PdfReader(file_path)
    text_parts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text_parts.append(t)
    return "\n".join(text_parts)

def split_text(text: str):
    """文本切分，优先按段落和中文标点切"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", ".", "！", "？", "，", " ", ""],
    )
    return splitter.split_text(text)

def get_collection_name(filename: str) -> str:
    """为每个文档生成唯一的ChromaDB集合名"""
    h = hashlib.md5(filename.encode()).hexdigest()[:12]
    return f"doc_{h}"

def index_document(file_path: str, filename: str) -> dict:
    """处理PDF：提取文本 -> 切分 -> 向量化 -> 存入ChromaDB"""
    text = extract_text(file_path)
    chunks = split_text(text)
    if not chunks:
        raise ValueError("PDF中未能提取到文本内容，可能是扫描版PDF")

    collection_name = get_collection_name(filename)

    # 删除同名旧集合（支持重复上传覆盖）
    try:
        chroma_client.delete_collection(collection_name)
    except Exception:
        pass

    collection = chroma_client.create_collection(name=collection_name)

    # fastembed 批量编码
    embeddings = list(embedding_model.embed(chunks))

    collection.add(
        ids=[f"chunk_{i}" for i in range(len(chunks))],
        embeddings=[e.tolist() for e in embeddings],
        documents=chunks,
    )

    return {
        "chunk_count": len(chunks),
        "total_chars": len(text),
        "collection_name": collection_name,
    }

def search(query: str, collection_name: str, top_k: int = TOP_K_RETRIEVAL):
    """向量检索：用问题向量去ChromaDB中找最相似的文本块"""
    collection = chroma_client.get_collection(name=collection_name)
    query_embedding = list(embedding_model.embed([query]))[0].tolist()
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
    docs = results.get("documents", [[]])[0]
    return docs