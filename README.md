# PDF-QA — AI-Powered Document Q&A System

基于 **LangChain + Milvus + DeepSeek** 的智能文档问答系统，支持 PDF 上传、RAG 检索增强生成、以及简历智能优化分析。

## 技术栈

| 层级 | 技术 |
|------|------|
| 框架 | FastAPI + LangChain |
| 向量数据库 | **Milvus Lite**（嵌入式，零部署，无需外部服务） |
| 嵌入模型 | BAAI/bge-small-zh-v1.5（HuggingFaceEmbeddings） |
| LLM | DeepSeek（通过 LangChain ChatOpenAI 兼容接口） |
| RAG 管道 | LangChain LCEL（LangChain Expression Language） |
| 文本切分 | RecursiveCharacterTextSplitter（中文语义切分） |
| 元数据存储 | SQLite + SQLAlchemy（异步） |
| 前端 | 原生 HTML/CSS/JS（零框架依赖） |

## 项目结构

```
PDF-QA/
├── app/
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 全局配置
│   ├── database.py          # SQLAlchemy 异步数据库
│   ├── models.py            # 数据模型
│   ├── pdf_processor.py     # PDF 解析 → 切分 → 向量化 → Milvus 索引
│   ├── rag_engine.py        # LCEL RAG 问答管道
│   ├── deepseek_client.py   # DeepSeek LLM（ChatOpenAI）
│   ├── resume_service.py    # 简历解析/分析/优化
│   └── routers/
│       ├── upload.py        # PDF 上传 API
│       ├── qa.py            # 问答 & 历史 API
│       └── resume.py        # 简历优化 API
├── frontend/                # 前端页面
├── uploads/                 # PDF 上传目录
├── milvus_db/               # Milvus 向量数据（本地文件）
├── requirements.txt
└── .env
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env`：

```env
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
```

### 3. 启动服务

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8899
```

首次运行自动下载 HuggingFace 嵌入模型（约 100MB），后续启动即用。

### 4. 打开界面

浏览器访问 `http://127.0.0.1:8899`

## 核心功能

### PDF 文档问答（RAG）

1. 上传 PDF → 自动提取文本、语义切分、向量化存入 Milvus
2. 输入问题 → 向量检索最相关片段 → DeepSeek 基于上下文生成答案
3. 支持问答历史回溯

**架构流程**：

```
PDF 上传 → pypdf 提取文本 → RecursiveCharacterTextSplitter 语义切分
→ HuggingFaceEmbeddings 向量化 → Milvus 存储
     ↓
用户提问 → 问题向量化 → Milvus 相似度检索（COSINE）
→ Top-K 片段拼接上下文 → DeepSeek LLM 生成答案
```

### 简历智能优化

- **简历解析**：自动识别个人信息、教育背景、工作经历、技能等板块
- **简历分析**：7 维度 AI 评估（评分、排版、内容质量、亮点、不足、建议、岗位方向）
- **多策略优化**：
  - 通用优化 — 语言流畅、逻辑清晰
  - 专业风格 — 用词精准、突出成果数据
  - 技术能力强化 — STAR 法则 + 量化指标
  - 岗位适配 — 针对目标 JD 定制
- **按板块优化**：支持单独优化项目经验、技能、自我评价等

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/upload` | 上传 PDF |
| POST | `/api/ask` | 文档问答 |
| GET | `/api/documents` | 文档列表 |
| GET | `/api/history/{doc_id}` | 问答历史 |
| POST | `/api/resume/analyze` | 简历分析 |
| POST | `/api/resume/optimize` | 简历优化 |

## 技术亮点

- **Milvus Lite**：嵌入式运行，零部署零外部服务，同一套 API 可无缝升级到 Milvus 集群版
- **中文语义切分**：自定义分隔符优先级 `\n\n → \n → 。→ . → ！→ ？`，保证每个 chunk 语义完整
- **LCEL 管道**：`retriever | prompt | llm | StrOutputParser`，代码清晰可扩展
- **多文档隔离**：每份 PDF 独立 Milvus collection，MD5 哈希命名，互不干扰

## License

MIT