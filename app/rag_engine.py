from app.deepseek_client import chat as deepseek_chat
from app.pdf_processor import search

async def ask(question: str, collection_name: str) -> dict:
    # Step 1: 向量检索
    retrieved_docs = search(question, collection_name)

    if not retrieved_docs:
        return {
            "answer": "文档中未找到相关内容，请尝试换个问法。",
            "sources": [],
        }

    # Step 2: 拼接上下文
    context = "\n\n---\n\n".join(
        f"[片段{i+1}] {doc}" for i, doc in enumerate(retrieved_docs)
    )

    # Step 3: 调用大模型
    answer = await deepseek_chat(context=context, question=question)

    return {
        "answer": answer,
        "sources": retrieved_docs,
    }
