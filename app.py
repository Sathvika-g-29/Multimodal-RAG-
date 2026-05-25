from pathlib import Path

import streamlit as st

from retriever.retriever import RetrievalRequest, retrieve_context
from llm.generator import generate_answer


st.set_page_config(
    page_title="Placement Intelligence Assistant",
    page_icon="",
    layout="wide",
)


DATA_DIR = Path("data")


def main() -> None:
    st.title("Placement Intelligence Assistant")
    st.caption("Grounded answers across placement tables, experiences, charts, and trends.")

    with st.sidebar:
        st.header("Retrieval controls")
        company = st.text_input("Company filter")
        year = st.text_input("Year filter")
        top_k = st.slider("Evidence chunks", min_value=2, max_value=10, value=5)

    query = st.chat_input("Ask about eligibility, trends, interview rounds, offers, or comparisons")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if query:
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        metadata = {
            "company": company.strip() or None,
            "year": year.strip() or None,
        }
        request = RetrievalRequest(query=query, top_k=top_k, metadata=metadata)
        evidence = retrieve_context(request)
        answer = generate_answer(query=query, evidence=evidence)

        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)


if __name__ == "__main__":
    main()

