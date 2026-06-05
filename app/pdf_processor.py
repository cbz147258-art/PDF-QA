"""PDF 处理模块 —— 基于 LangChain 全家桶：提取 → 切分 → 向量化 → 存入 ChromaDB"""
import os
import hashlib
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from app.config import (
    CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL_NAME,
    CHROMA_PERSIST_DIR, TOP_K_RETRIEVAL
)

# LangChain HuggingFace 嵌入模型（自动下载 BGE 中文模型）
embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL_NAME,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)


def extract_text(file_path: str) -> str:
    """从 PDF 中提取纯文本"""
    reader = PdfReader(file_path)
    text_parts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text_parts.append(t)
    return "\n".join(text_parts)


def split_text(text: str) -> list[str]:
    """文本切分：优先按段落和中文标点切分"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "\u3002", ".", "\uff01", "\uff1f", "\uff1b", " ", ""],
    )
    return splitter.split_text(text)


def get_collection_name(filename: str) -> str:
    """为每个文档生成唯一的 ChromaDB 集合名称"""
    h = hashlib.md5(filename.encode()).hexdigest()[:12]
    return f"doc_{h}"


def index_document(file_path: str, filename: str) -> dict:
    """处理 PDF：提取文本 → 切分 → 向量化 → 存入 ChromaDB（LangChain 风格）"""
    text = extract_text(file_path)
    chunks = split_text(text)
    if not chunks:
        raise ValueError("PDF 中未能提取到文本内容，可能是扫描版 PDF")

    collection_name = get_collection_name(filename)

    # 使用 LangChain Chroma wrapper：直接 from_texts 创建/覆盖集合
    Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory=CHROMA_PERSIST_DIR,
    )

    return {
        "chunk_count": len(chunks),
        "total_chars": len(text),
        "collection_name": collection_name,
    }


def search(query: str, collection_name: str, top_k: int = TOP_K_RETRIEVAL) -> list[str]:
    """向量检索：用问题去 ChromaDB 中找最相似的文本块（LangChain 风格）"""
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
    )
    docs = vectorstore.similarity_search(query, k=top_k)
    return [doc.page_content for doc in docs]