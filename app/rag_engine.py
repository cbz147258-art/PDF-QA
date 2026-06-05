"""RAG QA Engine - LangChain LCEL (LangChain Expression Language) RAG pipeline"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from app.config import CHROMA_PERSIST_DIR, EMBEDDING_MODEL_NAME, TOP_K_RETRIEVAL
from app.deepseek_client import llm

# RAG Prompt template
RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a smart document assistant. Answer based on the provided document content.\n\n"
        "Rules:\n"
        "1. Only answer using the document content provided, do not make up information\n"
        "2. If the document has no relevant info, honestly say 'Content not found in document'\n"
        "3. Be concise and clear, use bullet points when helpful\n"
        "4. Use 【】 to mark document citations\n\n"
        "Document content:\n{context}"
    )),
    ("user", "{question}"),
])


async def ask(question: str, collection_name: str) -> dict:
    """LangChain LCEL RAG QA: retrieve -> concat context -> LLM generate

    Args:
        question: user question
        collection_name: ChromaDB collection name (one per document)

    Returns:
        {"answer": str, "sources": list[str]}
    """
    # 1. Create vectorstore retriever
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K_RETRIEVAL})

    # 2. Retrieve relevant docs
    retrieved_docs = await retriever.ainvoke(question)

    if not retrieved_docs:
        return {
            "answer": "Content not found in document. Please try a different question.",
            "sources": [],
        }

    # 3. Build context from retrieved docs
    context = "\n\n---\n\n".join(
        f"[Chunk {i+1}] {doc.page_content}" for i, doc in enumerate(retrieved_docs)
    )
    sources = [doc.page_content for doc in retrieved_docs]

    # 4. LCEL chain: prompt -> llm -> output_parser
    chain = RAG_PROMPT | llm | StrOutputParser()
    answer = await chain.ainvoke({"context": context, "question": question})

    return {
        "answer": answer,
        "sources": sources,
    }