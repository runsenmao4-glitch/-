# Equity-AI 股权知识库 Web PoC 开发介绍

## 项目定位

Equity-AI 是一个面向股权服务场景的本地知识库问答 PoC，覆盖 ESOP、期权、股权回购、股权代持、分红退出、合规政策和财税提示等问题。系统采用 RAG（Retrieval-Augmented Generation）架构：先从本地文档检索相关片段，再交由大模型生成回答。

项目核心原则是数据本地处理和敏感信息保护。原始 PDF/DOCX 文件只放在本机 `data/` 目录，向量库持久化在本机 `db/` 目录，Git 仓库只保存代码框架、依赖清单和配置模板，不保存 API Key、原始资料或向量库文件。

## 技术栈

- Python 3.10+
- Streamlit：Web 聊天界面
- LangChain：文档加载、文本切分、Embedding、LLM 调用和检索编排
- ChromaDB：本地持久化向量数据库
- PyPDF / docx2txt：PDF 与 Word 文档解析
- OpenAI 兼容 API：用于 Embedding 和 Chat LLM，可接入 OpenAI 或兼容网关

## 代码结构

```text
equity_ai_poc/
  data/              # 本地原始 PDF/DOCX，不提交到 Git
  db/                # ChromaDB 本地向量库，不提交到 Git
  ingest.py          # 文档读取、脱敏、切分、向量化入库
  rag_pipeline.py    # 检索、Prompt 组装、LLM 问答逻辑
  app.py             # Streamlit Web 聊天界面
  requirements.txt   # Python 依赖
  .env.example       # 环境变量模板，可提交
  .env               # 本地密钥配置，不提交
```

## 核心流程

1. 将 PDF 或 DOCX 文件放入 `data/`。
2. 运行 `python ingest.py`。
3. `ingest.py` 会读取文档，并在文本切分前执行正则脱敏：
   - 18 位身份证号替换为 `【脱敏身份证】`
   - 11 位手机号替换为 `【脱敏手机号】`
   - 具体金额替换为 `【脱敏金额】`
4. 文本使用 `RecursiveCharacterTextSplitter` 切分，参数为 `chunk_size=800`、`chunk_overlap=150`。
5. 切片通过 OpenAI 兼容 Embedding 写入本地 ChromaDB。
6. 用户在 Streamlit 页面提问后，系统从 ChromaDB 相似度检索 Top K=4 的片段，并基于片段生成回答。

## Web 功能

Streamlit 应用提供类似 AI 助手的聊天界面，并在侧边栏提供两种模式：

- 内部模式：回答更详尽，允许展示内部条款编号、制度名称和来源信息。
- 外部模式：回答更精简，偏客服口吻，不展示具体条款编号或内部制度编号。

回答完成后，页面会使用折叠面板展示参考来源，包括本地文档名称、页码或位置，以及检索到的具体片段。

## 合规与计算约束

系统 Prompt 将 AI 角色固定为“专业股权合规与财税专家”。对于股权比例、成熟度、归属/解锁、行权成本、税务测算等计算类问题，回答必须列出计算公式，并包含以下免责声明：

```text
结果仅供参考，最终以系统算力为准。
```

如果知识库资料不足，系统应明确说明无法从当前知识库确认，避免把通用模型知识包装成内部依据。

## 本地运行

安装依赖：

```powershell
python -m pip install -r requirements.txt
```

复制并填写环境变量：

```powershell
Copy-Item .env.example .env
```

至少需要配置：

```text
OPENAI_API_KEY=你的 API Key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

执行入库：

```powershell
python ingest.py
```

启动 Web 应用：

```powershell
streamlit run app.py
```

## Git 提交策略

提交到 Git 的内容只包含代码框架和说明文档：

- 提交：`app.py`、`ingest.py`、`rag_pipeline.py`、`requirements.txt`、`.env.example`、`.gitignore`、`DEVELOPMENT.md`
- 不提交：`.env`、`data/` 原始文档、`db/` 向量库、`__pycache__/` 缓存

这样可以避免 API Key、客户资料、脱敏前原始文本和本地向量索引进入远程仓库。
