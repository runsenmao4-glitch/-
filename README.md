Equity-AI 股权知识库 Web PoC
基于本地文档的股权服务 RAG 知识库 Web PoC，支持 PDF/DOCX 脱敏入库、ChromaDB 本地向量检索、Streamlit 聊天问答、内外部模式切换与文档溯源。

项目简介
Equity-AI 面向股权服务测试场景，适用于 ESOP、期权、股权回购、股权代持、分红退出、合规政策和财税提示等知识问答。系统会读取本地 data/ 目录中的 PDF/DOCX 文档，在文本切分前完成敏感信息脱敏，再写入本地 ChromaDB 向量库。

用户通过 Streamlit Web 页面提问后，系统会检索本地知识库中最相关的片段，并调用 OpenAI 兼容 API 生成回答。

核心功能
本地 PDF/DOCX 文档读取
身份证号、手机号、金额字段正则脱敏
ChromaDB 本地持久化向量库
LangChain RAG 检索问答
OpenAI 兼容 Chat 与 Embedding API
Streamlit Chat UI
内部模式 / 外部模式切换
回答后展示本地文档来源和参考片段
计算类问题强制输出公式和免责声明
技术栈
Python 3.10+
Streamlit
LangChain
ChromaDB
PyPDF
docx2txt
OpenAI compatible API
目录结构
equity_ai_poc/
  data/                  # 原始 PDF/DOCX，本地使用，不提交到 Git
  db/                    # ChromaDB 本地向量库，不提交到 Git
  ingest.py              # 数据脱敏与入库脚本
  rag_pipeline.py        # 核心检索与对话逻辑
  app.py                 # Streamlit 前端应用
  requirements.txt       # 依赖清单
  .env.example           # 环境变量模板
  DEVELOPMENT.md         # 开发说明
快速开始
安装依赖：

python -m pip install -r requirements.txt
复制环境变量模板：

Copy-Item .env.example .env
编辑 .env，填写 OpenAI 兼容 API 配置：

OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
CHROMA_DB_DIR=./db
DATA_DIR=./data
将 PDF/DOCX 文件放入 data/ 目录，然后执行入库：

python ingest.py
启动 Web 应用：

streamlit run app.py
使用模式
侧边栏提供两种访问模式：

内部模式：回答更详尽，允许展示内部条款编号、制度名称和来源信息。
外部模式：回答更精简，偏客服口吻，不展示具体条款编号或内部制度编号。
每次回答后，页面会在折叠面板中展示参考来源，包括文档名称、页码或位置，以及检索到的本地片段。

数据安全
本项目默认不提交以下内容：

.env API Key 配置
data/ 原始文档
db/ 本地向量库
Python 缓存文件
入库流程会在文本切分前执行脱敏：

18 位身份证号 -> 【脱敏身份证】
11 位手机号 -> 【脱敏手机号】
具体金额 -> 【脱敏金额】
计算类回答约束
当问题涉及股权比例、成熟度、归属/解锁、行权成本或税务测算时，系统 Prompt 要求模型输出计算公式，并包含以下声明：

结果仅供参考，最终以系统算力为准。
说明
这是一个 PoC 项目，用于验证本地文档知识库、脱敏入库、RAG 检索和 Web 问答流程。生产使用前，需要进一步补充权限控制、日志审计、模型调用限流、测试覆盖和更严格的合规审查。


C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe

C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe


