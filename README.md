# PDF-QA 智能问答机器人

基于 **LangChain + ChromaDB + DeepSeek** 的智能文档问答系统，支持 PDF 上传、RAG 检索增强生成、以及简历优化分析。

## 技术栈

| 层级 | 技术 |
|------|------|
| 框架 | FastAPI + LangChain |
| 向量数据库 | ChromaDB（本地持久化） |
| 嵌入模型 | BAAI/bge-small-zh-v1.5（HuggingFace） |
| LLM | DeepSeek（通过 LangChain ChatOpenAI 兼容接口） |
| 文本切分 | LangChain RecursiveCharacterTextSplitter |
| RAG 管道 | LangChain LCEL（LangChain Expression Language） |
| 元数据存储 | SQLite + SQLAlchemy（异步） |
| 前端 | 原生 HTML/CSS/JS |

## 项目结构

```
PDF-QA/
├── app/
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理（API Key、模型参数等）
│   ├── database.py          # SQLAlchemy 异步数据库连接
│   ├── models.py            # 数据模型（Document、QARecord、ResumeRecord）
│   ├── pdf_processor.py     # PDF 解析、文本切分、向量化与 ChromaDB 索引
│   ├── rag_engine.py        # LCEL RAG 问答管道
│   ├── deepseek_client.py   # DeepSeek LLM 客户端（LangChain ChatOpenAI）
│   ├── resume_service.py    # 简历解析、分析、优化服务
│   └── routers/
│       ├── upload.py        # PDF 上传 API
│       ├── qa.py            # 问答 & 历史记录 API
│       └── resume.py        # 简历优化 API
├── frontend/
│   ├── index.html           # 前端页面
│   ├── app.js               # 前端逻辑
│   └── style.css            # 样式
├── uploads/                 # PDF 上传目录
├── chroma_db/               # ChromaDB 向量数据持久化目录
├── requirements.txt         # Python 依赖
└── .env                     # 环境变量配置
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件：

```env
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
```

### 3. 启动服务

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8899
```

首次运行会自动从 HuggingFace 下载嵌入模型（约 100MB），后续启动即用。

### 4. 打开界面

浏览器访问 `http://127.0.0.1:8899`

## 功能模块

### PDF 文档问答（RAG）

1. 上传 PDF 文档 → 自动提取文本、切分、向量化存入 ChromaDB
2. 输入问题 → 向量检索最相关片段 → DeepSeek 基于上下文生成答案
3. 支持问答历史记录查看

### 简历优化（Resume Skill）

- **简历解析**：自动识别个人信息、教育背景、工作经历、技能等板块
- **简历分析**：AI 从 7 个维度全面评估简历质量
- **简历优化**：支持 4 种策略
  - 通用优化 —— 语言流畅、逻辑清晰
  - 专业风格 —— 用词精准、突出成果
  - 突出技术能力 —— 强调技术栈深度与工程能力
  - 适配特定岗位 —— 针对目标 JD 定制化优化

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/upload` | 上传 PDF |
| POST | `/api/ask` | 文档问答 |
| GET | `/api/documents` | 文档列表 |
| GET | `/api/history/{doc_id}` | 问答历史 |
| POST | `/api/resume/analyze` | 简历分析 |
| POST | `/api/resume/optimize` | 简历优化 |

## License

MIT