import streamlit as st

from src.rag import answer_question

# Protótipo para testes, apagar/editar isso posteriormente

st.set_page_config(
    page_title="GearMind",
    layout="wide"
)

st.title("GearMind")

question = st.text_input(
    "Digite sua dúvida:"
)

if st.button("Consultar"):

    response = answer_question(question)

    st.markdown(response)