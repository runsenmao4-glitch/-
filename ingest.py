from pathlib import Path
import os
import re

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


PROJECT_ROOT = Path(__file__).resolve().parent
COLLECTION_NAME = "equity_ai_knowledge"

ID_CARD_PATTERN = re.compile(r"(?<!\d)\d{17}[\dXx](?!\w)")
PHONE_PATTERN = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
AMOUNT_PATTERN = re.compile(
    r"(?<![\w.])(?:人民币|RMB|¥)?\s*\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:万元|元|万|亿元|千元)(?!\w)"
    r"|(?<![\w.])(?:人民币|RMB|¥)?\s*\d+(?:\.\d+)?\s*(?:万元|元|万|亿元|千元)(?!\w)"
)


def resolve_path(value: str | None, default: str) -> Path:
    raw_path = Path(value or default)
    if raw_path.is_absolute():
        return raw_path
    return PROJECT_ROOT / raw_path


def sanitize_text(text: str) -> str:
    sanitized = ID_CARD_PATTERN.sub("【脱敏身份证】", text)
    sanitized = PHONE_PATTERN.sub("【脱敏手机号】", sanitized)
    sanitized = AMOUNT_PATTERN.sub("【脱敏金额】", sanitized)
    return sanitized


def load_documents(data_dir: Path) -> list[Document]:
    documents: list[Document] = []
    files = sorted([*data_dir.glob("*.pdf"), *data_dir.glob("*.docx")])

    for file_path in files:
        loader = PyPDFLoader(str(file_path)) if file_path.suffix.lower() == ".pdf" else Docx2txtLoader(str(file_path))
        for document in loader.load():
            document.page_content = sanitize_text(document.page_content)
            document.metadata["source"] = str(file_path)
            document.metadata["file_name"] = file_path.name
            documents.append(document)

    return documents


def split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n\n", "\n", "。", "；", ";", "，", ",", " ", ""],
    )
    return splitter.split_documents(documents)


def create_embeddings() -> OpenAIEmbeddings:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "replace-with-your-api-key":
        raise RuntimeError("请先在 .env 中配置 OPENAI_API_KEY。")

    return OpenAIEmbeddings(
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    )


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")

    data_dir = resolve_path(os.getenv("DATA_DIR"), "./data")
    db_dir = resolve_path(os.getenv("CHROMA_DB_DIR"), "./db")
    data_dir.mkdir(parents=True, exist_ok=True)
    db_dir.mkdir(parents=True, exist_ok=True)

    documents = load_documents(data_dir)
    if not documents:
        print(f"未在 {data_dir} 找到 PDF 或 DOCX 文件。请放入文档后重新运行 python ingest.py。")
        return

    chunks = split_documents(documents)
    if not chunks:
        print("文档已读取，但没有产生可入库的文本片段。")
        return

    embeddings = create_embeddings()
    existing_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(db_dir),
    )
    try:
        existing_store.delete_collection()
    except ValueError:
        pass

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(db_dir),
    )
    print(f"入库完成：{len(documents)} 个文档页/段，{len(chunks)} 个切片，持久化目录：{db_dir}")


if __name__ == "__main__":
    main()
