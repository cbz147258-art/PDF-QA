"""PDF processor - pymilvus MilvusClient (Lite) for vector storage"""
import hashlib
import os
import time
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from pymilvus import MilvusClient
from app.config import (
    CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL_NAME,
    MILVUS_DB_PATH, TOP_K_RETRIEVAL
)

embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL_NAME,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)

_milvus_client = None

def _get_client() -> MilvusClient:
    global _milvus_client
    if _milvus_client is None:
        os.makedirs(os.path.dirname(MILVUS_DB_PATH), exist_ok=True)
        _milvus_client = MilvusClient(uri=MILVUS_DB_PATH)
    return _milvus_client


def extract_text(file_path: str) -> str:
    """Extract plain text from PDF"""
    reader = PdfReader(file_path)
    text_parts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text_parts.append(t)
    return "\n".join(text_parts)


def split_text(text: str) -> list[str]:
    """Split text by semantic boundaries"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "\u3002", ".", "\uff01", "\uff1f", "\uff1b", " ", ""],
    )
    return splitter.split_text(text)


def get_collection_name(filename: str) -> str:
    """Generate unique Milvus collection name per document"""
    h = hashlib.md5(filename.encode()).hexdigest()[:12]
    return f"doc_{h}"


def index_document(file_path: str, filename: str) -> dict:
    """Process PDF: extract -> split -> embed -> store in Milvus"""
    text = extract_text(file_path)
    chunks = split_text(text)
    if not chunks:
        raise ValueError("No text extracted from PDF, possibly scanned PDF")

    collection_name = get_collection_name(filename)
    client = _get_client()

    # Drop existing collection for re-upload
    if client.has_collection(collection_name):
        client.drop_collection(collection_name)

    # Generate embeddings
    chunk_embeddings = [embeddings.embed_query(c) for c in chunks]

    # Prepare data
    data = [
        {"id": i, "vector": chunk_embeddings[i], "text": chunks[i]}
        for i in range(len(chunks))
    ]

    # Create collection with COSINE metric and insert data
    client.create_collection(
        collection_name=collection_name,
        dimension=len(chunk_embeddings[0]),
        metric_type="COSINE",
    )
    client.insert(collection_name=collection_name, data=data)

    return {
        "chunk_count": len(chunks),
        "total_chars": len(text),
        "collection_name": collection_name,
    }


def search(query: str, collection_name: str, top_k: int = TOP_K_RETRIEVAL) -> list[str]:
    """Vector search: find most similar text chunks in Milvus"""
    client = _get_client()

    # Load collection for searching
    client.load_collection(collection_name)

    query_embedding = [embeddings.embed_query(query)]

    results = client.search(
        collection_name=collection_name,
        data=query_embedding,
        limit=top_k,
        output_fields=["text"],
    )

    return [hit["entity"]["text"] for hit in results[0]]