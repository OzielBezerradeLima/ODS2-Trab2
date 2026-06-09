MODEL_NAME = "qwen2.5:7b"


def generate(prompt: str) -> str:
    try:
        from ollama import chat
    except ImportError as exc:
        raise RuntimeError("Pacote ollama nao instalado no ambiente Python.") from exc

    response = chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return response["message"]["content"]
