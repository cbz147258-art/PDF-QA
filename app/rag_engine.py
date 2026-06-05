"""RAG QA Engine - LangChain LCEL with pymilvus MilvusClient"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_huggingface import HuggingFaceEmbeddings
from pymilvus import MilvusClient
from app.config import MILVUS_DB_PATH, EMBEDDING_MODEL_NAME, TOP_K_RETRIEVAL
from app.deepseek_client import llm
import os

RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a smart document assistant. Answer based on the provided document content.\n\n"
        "Rules:\n"
        "1. Only answer using the document content provided, do not make up information\n"
        "2. If the document has no relevant info, honestly say 'Content not found in document'\n"
        "3. Be concise and clear, use bullet points when helpful\n"
        "4. Use [] to mark document citations\n\n"
        "Document content:\n{context}"
    )),
    ("user", "{question}"),
])


async def ask(question: str, collection_name: str) -> dict:
    """LangChain LCEL RAG QA with Milvus Lite

    Args:
        question: user question
        collection_name: Milvus collection name

    Returns:
        {"answer": str, "sources": list[str]}
    """
    embeddings_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    client = MilvusClient(uri=MILVUS_DB_PATH)
    client.load_collection(collection_name)

    query_embedding = [embeddings_model.embed_query(question)]

    results = client.search(
        collection_name=collection_name,
        data=query_embedding,
        limit=TOP_K_RETRIEVAL,
        output_fields=["text"],
    )

    sources = [hit["entity"]["text"] for hit in results[0]] if results and results[0] else []

    if not sources:
        return {
            "answer": "Content not found in document. Please try a different question.",
            "sources": [],
        }

    context = "\n\n---\n\n".join(
        f"[Chunk {i+1}] {s}" for i, s in enumerate(sources)
    )

    chain = RAG_PROMPT | llm | StrOutputParser()
    answer = await chain.ainvoke({"context": context, "question": question})

    return {
        "answer": answer,
        "sources": sources,
    }