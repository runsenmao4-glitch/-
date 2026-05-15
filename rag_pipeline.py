from pathlib import Path
from typing import Any, Literal, TypedDict
import os

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


PROJECT_ROOT = Path(__file__).resolve().parent
COLLECTION_NAME = "equity_ai_knowledge"
Mode = Literal["内部模式", "外部模式"]


class RagResult(TypedDict):
    answer: str
    source_documents: list[Document]


def resolve_path(value: str | None, default: str) -> Path:
    raw_path = Path(value or default)
    if raw_path.is_absolute():
        return raw_path
    return PROJECT_ROOT / raw_path


def has_chroma_data(db_dir: Path) -> bool:
    return (db_dir / "chroma.sqlite3").exists() or any(db_dir.glob("*/index_metadata.pickle"))


def load_environment() -> None:
    load_dotenv(PROJECT_ROOT / ".env")


def create_embeddings() -> OpenAIEmbeddings:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "replace-with-your-api-key":
        raise RuntimeError("请先在 .env 中配置 OPENAI_API_KEY。")

    return OpenAIEmbeddings(
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    )


def create_llm() -> ChatOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "replace-with-your-api-key":
        raise RuntimeError("请先在 .env 中配置 OPENAI_API_KEY。")

    return ChatOpenAI(
        model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        temperature=0.2,
    )


def get_vector_store() -> Chroma:
    load_environment()
    db_dir = resolve_path(os.getenv("CHROMA_DB_DIR"), "./db")
    if not db_dir.exists() or not has_chroma_data(db_dir):
        raise RuntimeError("知识库尚未初始化。请先将文档放入 data/，再运行 python ingest.py。")

    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=create_embeddings(),
        persist_directory=str(db_dir),
    )


def _format_source(document: Document, index: int) -> str:
    file_name = document.metadata.get("file_name") or Path(document.metadata.get("source", "未知文档")).name
    page = document.metadata.get("page")
    location = f"第 {page + 1} 页" if isinstance(page, int) else "未知位置"
    return f"[{index}] {file_name}（{location}）\n{document.page_content}"


def _mode_instruction(mode: Mode) -> str:
    if mode == "内部模式":
        return "当前为内部模式：回答应详尽、专业，允许引用内部条款编号、制度名称和来源信息。"
    return "当前为外部模式：回答应精简、友好，偏客服口吻，不展示具体条款编号或内部制度编号。"


def _system_prompt(mode: Mode) -> str:
    return f"""你是专业股权合规与财税专家，基于本地知识库回答问题。

必须遵守：
1. 只基于提供的参考资料回答；资料不足时，明确说明无法从当前知识库确认。
2. {_mode_instruction(mode)}
3. 凡涉及股权比例、成熟度、归属/解锁、行权成本、税务测算等计算，必须列出计算公式，公式可使用 LaTeX。
4. 对所有计算类回答，必须包含原句：结果仅供参考，最终以系统算力为准。
5. 不输出身份证号、手机号、具体金额等敏感信息；若资料中出现脱敏占位符，保持占位符。
"""


def _build_context(documents: list[Document]) -> str:
    if not documents:
        return "当前没有检索到可用参考资料。"
    return "\n\n".join(_format_source(document, index) for index, document in enumerate(documents, start=1))


def ask(question: str, mode: Mode = "内部模式") -> RagResult:
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 4})
    source_documents = retriever.invoke(question)
    context = _build_context(source_documents)

    user_prompt = f"""参考资料：
{context}

用户问题：
{question}

请按当前模式回答。"""

    response = create_llm().invoke(
        [
            SystemMessage(content=_system_prompt(mode)),
            HumanMessage(content=user_prompt),
        ]
    )
    answer = response.content if isinstance(response.content, str) else str(response.content)
    return {"answer": answer, "source_documents": source_documents}


def knowledge_base_ready() -> tuple[bool, str]:
    load_environment()
    db_dir = resolve_path(os.getenv("CHROMA_DB_DIR"), "./db")
    if not db_dir.exists() or not has_chroma_data(db_dir):
        return False, "知识库尚未初始化。请先将 PDF/DOCX 放入 data/，再运行 python ingest.py。"

    try:
        store = get_vector_store()
        data: dict[str, Any] = store.get(limit=1)
    except Exception as exc:
        return False, f"知识库加载失败：{exc}"

    ids = data.get("ids", [])
    if not ids:
        return False, "知识库为空。请先运行 python ingest.py 重新入库。"
    return True, "知识库已就绪。"
