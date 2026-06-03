from openai import AsyncOpenAI
from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

async def chat(context: str, question: str) -> str:
    """调用DeepSeek进行RAG问答"""
    system_prompt = (
        "你是一个智能文档助手。请根据以下文档内容回答用户问题。\n\n"
        "规则：\n"
        "1. 只根据提供的文档内容回答，不要编造信息\n"
        "2. 如果文档中没有相关信息，诚实地说「文档中未找到相关内容」\n"
        "3. 回答要简洁清晰，必要时分点说明\n"
        "4. 引用文档内容时使用【】标注\n\n"
        f"文档内容：\n{context}"
    )

    response = await client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        temperature=0.3,
        max_tokens=2000,
    )
    return response.choices[0].message.content