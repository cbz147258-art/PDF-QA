"""DeepSeek LLM 客户端 —— 基于 LangChain ChatOpenAI 封装"""
from langchain_openai import ChatOpenAI
from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

# 全g局共享的 LangChain LLM 实例
llm = ChatOpenAI(
    model=DEEPSEEK_MODEL,
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
    temperature=0.3,
    max_tokens=2000,
)

# 兼容旧接口的异步聊天函数（供 rag_engine 使用）
async def chat(context: str, question: str) -> str:
    """调用 DeepSeek 进行 RAG 问答"""
    system_prompt = (
        "你是一个智能文档助手。请根据以下文档内容回答用户问题。\n\n"
        "规则：\n"
        "1. 只根据提供的文档内容回答，不要编造信息\n"
        "2. 如果文档中没有相关信息，诚实地说「文档中未找到相关内容」\n"
        "3. 回答要简洁清晰，必要时分点说明\n"
        "4. 引用文档内容时使用【】标注\n\n"
        f"文档内容：\n{context}"
    )
    response = await llm.ainvoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ])
    return response.content