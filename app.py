from typing import Any

import streamlit as st

from rag_pipeline import Mode, ask, knowledge_base_ready


st.set_page_config(page_title="Equity-AI 股权知识库", page_icon="EA", layout="wide")


def init_session_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []


def render_sources(source_documents: list[Any]) -> None:
    if not source_documents:
        return

    with st.expander("参考来源", expanded=False):
        for index, document in enumerate(source_documents, start=1):
            metadata = document.metadata
            file_name = metadata.get("file_name") or metadata.get("source", "未知文档")
            page = metadata.get("page")
            page_label = f"第 {page + 1} 页" if isinstance(page, int) else "未知位置"
            st.markdown(f"**{index}. {file_name} - {page_label}**")
            st.write(document.page_content)


init_session_state()

with st.sidebar:
    st.title("Equity-AI")
    mode: Mode = st.radio("访问模式", ["内部模式", "外部模式"], horizontal=False)
    ready, status = knowledge_base_ready()
    st.caption(status)
    if st.button("清空对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.title("股权知识库问答")

if not ready:
    st.warning("知识库尚未初始化。请将 PDF/DOCX 放入 data/ 目录后运行 `python ingest.py`。")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            render_sources(message.get("sources", []))

question = st.chat_input("请输入股权、期权、ESOP、合规或税务相关问题")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        if not ready:
            answer = "知识库尚未初始化。请先将 PDF/DOCX 放入 data/，再运行 `python ingest.py`。"
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer, "sources": []})
        else:
            with st.spinner("正在检索本地知识库并生成回答..."):
                try:
                    result = ask(question, mode)
                    st.markdown(result["answer"])
                    render_sources(result["source_documents"])
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": result["answer"],
                            "sources": result["source_documents"],
                        }
                    )
                except Exception as exc:
                    error_message = f"生成回答失败：{exc}"
                    st.error(error_message)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": error_message, "sources": []}
                    )
