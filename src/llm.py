import os

from ollama import chat


MODEL_NAME = os.getenv("RAG_PRIMARY_MODEL", "qwen2.5:7b")


def generate(prompt: str, model_name: str | None = None) -> str:
    selected_model = model_name or MODEL_NAME

    response = chat(
        model=selected_model,
        messages=[{"role": "user", "content": prompt}],
    )

    return response["message"]["content"]
