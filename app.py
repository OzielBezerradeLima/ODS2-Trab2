from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

from rag_client import DEVICE_OPTIONS, GAME_OPTIONS, answer_question


APP_TITLE = "GearMind RAG Wiki"


def setup_page() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="GM",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        """
        <style>
            .block-container {
                max-width: 1120px;
                padding-top: 1.4rem;
                padding-bottom: 2.5rem;
            }

            [data-testid="stSidebar"] {
                border-right: 1px solid rgba(49, 51, 63, 0.16);
            }

            .gm-title {
                font-size: 1.75rem;
                line-height: 1.2;
                font-weight: 700;
                margin-bottom: 0.2rem;
            }

            .gm-subtitle {
                color: rgba(49, 51, 63, 0.68);
                margin-bottom: 1.2rem;
            }

            .source-line {
                border-left: 3px solid #1f9d77;
                padding: 0.15rem 0 0.15rem 0.75rem;
                margin: 0.35rem 0 0.6rem 0;
            }

            .source-title {
                font-weight: 650;
                margin-bottom: 0.1rem;
            }

            .source-meta {
                color: rgba(49, 51, 63, 0.72);
                font-size: 0.9rem;
            }

            .history-item {
                border-bottom: 1px solid rgba(49, 51, 63, 0.12);
                padding: 0.45rem 0;
                font-size: 0.92rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "history" not in st.session_state:
        st.session_state.history = []


def format_option(option: dict[str, str]) -> str:
    return option["label"]


def selected_value(option: dict[str, str]) -> str:
    return option["value"]


def render_sources(sources: list[dict]) -> None:
    if not sources:
        return

    with st.expander("Fontes utilizadas", expanded=True):
        for index, source in enumerate(sources, start=1):
            score = source.get("score")
            score_text = f" - similaridade {score:.2f}" if isinstance(score, float) else ""
            page = source.get("page", "n/a")

            st.markdown(
                f"""
                <div class="source-line">
                    <div class="source-title">{index}. {source.get("source", "Fonte desconhecida")}</div>
                    <div class="source-meta">
                        Página {page} - {source.get("document_type", "documento")}
                        - {source.get("device", "geral")}
                        - tópico: {source.get("topic", "n/a")}{score_text}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            excerpt = source.get("content")
            if excerpt:
                st.caption(excerpt.strip())


def render_sidebar() -> tuple[str, str, int]:
    with st.sidebar:
        st.header("Filtros")

        device_option = st.selectbox(
            "Notebook",
            DEVICE_OPTIONS,
            index=0,
            format_func=format_option,
        )

        game_option = st.selectbox(
            "Jogo",
            GAME_OPTIONS,
            index=0,
            format_func=format_option,
        )

        top_k = st.slider("Quantidade de fontes", min_value=2, max_value=8, value=5)

        if st.button("Limpar histórico", use_container_width=True):
            st.session_state.messages = []
            st.session_state.history = []
            st.rerun()

        st.divider()
        st.subheader("Histórico")

        if not st.session_state.history:
            st.caption("Nenhuma consulta registrada.")
        else:
            for item in reversed(st.session_state.history[-6:]):
                st.markdown(
                    f"""
                    <div class="history-item">
                        <strong>{item["time"]}</strong><br>
                        {item["question"]}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.download_button(
                "Exportar histórico",
                data=json.dumps(st.session_state.history, ensure_ascii=False, indent=2),
                file_name="gearmind_historico_consultas.json",
                mime="application/json",
                use_container_width=True,
            )

    return selected_value(device_option), selected_value(game_option), top_k


def render_chat_history() -> None:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                render_sources(message.get("sources", []))


def main() -> None:
    setup_page()
    init_state()

    device, game, top_k = render_sidebar()

    st.markdown(f'<div class="gm-title">{APP_TITLE}</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="gm-subtitle">Consulta técnica para notebooks gamer, drivers e ajustes de desempenho.</div>',
        unsafe_allow_html=True,
    )

    render_chat_history()

    question = st.chat_input("Pergunte sobre RAM, drivers, stuttering, undervolt ou compatibilidade")
    if not question:
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Buscando fontes e preparando resposta..."):
            result = answer_question(
                question=question,
                device=device,
                game=game,
                top_k=top_k,
            )

        answer = result["answer"]
        sources = result.get("sources", [])
        st.markdown(answer)
        render_sources(sources)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "sources": sources,
        }
    )

    st.session_state.history.append(
        {
            "time": datetime.now().strftime("%H:%M"),
            "question": question,
            "answer": answer,
            "device": device,
            "game": game,
            "sources": sources,
        }
    )


if __name__ == "__main__":
    main()
