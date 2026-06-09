from __future__ import annotations

import math
import re
from collections import Counter


DEVICE_OPTIONS = [
    {"label": "Todos", "value": "all"},
    {"label": "Lenovo LOQ", "value": "lenovo_loq"},
    {"label": "Acer Nitro", "value": "acer_nitro"},
    {"label": "Asus TUF", "value": "asus_tuf"},
]

GAME_OPTIONS = [
    {"label": "Todos", "value": "all"},
    {"label": "Elden Ring", "value": "elden_ring"},
    {"label": "Cyberpunk 2077", "value": "cyberpunk_2077"},
    {"label": "Valorant", "value": "valorant"},
    {"label": "Forza Horizon", "value": "forza_horizon"},
]


MOCK_CHUNKS = [
    {
        "id": "chunk_001",
        "content": "Supports up to 32 GB DDR5 memory.",
        "metadata": {
            "source": "Lenovo LOQ User Guide",
            "page": 14,
            "device": "lenovo_loq",
            "document_type": "manual",
            "topic": "ram",
        },
    },
    {
        "id": "chunk_102",
        "content": "Fixed stuttering issues in Elden Ring when using DLSS.",
        "metadata": {
            "source": "NVIDIA Driver 555.85",
            "page": 1,
            "device": "generic",
            "document_type": "driver_notes",
            "topic": "elden_ring",
        },
    },
    {
        "id": "chunk_245",
        "content": "Stable undervolt: CPU offset -120mV. GPU offset -100mV.",
        "metadata": {
            "source": "Reddit r/LenovoLOQ",
            "page": 1,
            "device": "lenovo_loq",
            "document_type": "forum",
            "topic": "undervolt",
        },
    },
    {
        "id": "chunk_310",
        "content": "Acer Nitro models may require BIOS and GPU driver updates before testing performance issues.",
        "metadata": {
            "source": "Acer Nitro Support Notes",
            "page": 3,
            "device": "acer_nitro",
            "document_type": "manual",
            "topic": "drivers",
        },
    },
    {
        "id": "chunk_411",
        "content": "Asus TUF Gaming notebooks include performance profiles that affect fan speed, temperature and clock behavior.",
        "metadata": {
            "source": "Asus TUF Gaming User Guide",
            "page": 22,
            "device": "asus_tuf",
            "document_type": "manual",
            "topic": "performance",
        },
    },
]

STOPWORDS = {
    "a",
    "ao",
    "as",
    "com",
    "da",
    "de",
    "do",
    "dos",
    "e",
    "em",
    "o",
    "os",
    "para",
    "qual",
    "que",
    "um",
    "uma",
}

TOPIC_SYNONYMS = {
    "ram": {"ram", "memoria", "memory", "ddr5", "gb"},
    "undervolt": {"undervolt", "offset", "mv", "voltagem", "temperatura"},
    "elden_ring": {"elden", "ring", "dlss", "stuttering", "travamento", "engasgo"},
    "drivers": {"driver", "drivers", "bios", "nvidia", "amd", "update"},
    "performance": {"performance", "desempenho", "fan", "clock", "temperatura"},
}

OFF_TOPIC_TERMS = {"bolo", "receita", "cozinha", "ingrediente", "assar"}


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    return [word for word in words if word not in STOPWORDS and len(word) > 1]


def cosine_similarity(left: Counter, right: Counter) -> float:
    common = set(left) & set(right)
    numerator = sum(left[word] * right[word] for word in common)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


def infer_topics(question_tokens: set[str]) -> set[str]:
    topics = set()
    for topic, synonyms in TOPIC_SYNONYMS.items():
        if question_tokens & synonyms:
            topics.add(topic)
    return topics


def search(question: str, device: str = "all", game: str = "all", top_k: int = 5) -> list[dict]:
    question_tokens = tokenize(question)
    question_vector = Counter(question_tokens)
    inferred_topics = infer_topics(set(question_tokens))
    results = []

    for chunk in MOCK_CHUNKS:
        metadata = chunk["metadata"]
        chunk_text = f'{chunk["content"]} {metadata["source"]} {metadata["topic"]} {metadata["device"]}'
        score = cosine_similarity(question_vector, Counter(tokenize(chunk_text)))

        if device != "all" and metadata["device"] in {device, "generic"}:
            score += 0.12
        if game != "all" and metadata["topic"] == game:
            score += 0.16
        if metadata["topic"] in inferred_topics:
            score += 0.2

        if score > 0:
            results.append(
                {
                    "id": chunk["id"],
                    "content": chunk["content"],
                    "score": min(score, 1.0),
                    **metadata,
                }
            )

    return sorted(results, key=lambda item: item["score"], reverse=True)[:top_k]


def answer_question(question: str, device: str = "all", game: str = "all", top_k: int = 5) -> dict:
    question_tokens = set(tokenize(question))
    if question_tokens & OFF_TOPIC_TERMS:
        return {
            "answer": (
                "Não encontrei informação suficiente nas fontes técnicas do projeto para responder "
                "essa pergunta. A base atual é voltada a notebooks gamer, drivers, jogos e ajustes "
                "de desempenho."
            ),
            "sources": [],
            "backend": "mock",
        }

    sources = search(question=question, device=device, game=game, top_k=top_k)
    if not sources:
        return {
            "answer": (
                "Não encontrei trechos relevantes na base disponível. Quando o pipeline RAG completo "
                "for conectado, esta resposta deverá vir do Qwen2.5:7B usando apenas os chunks recuperados."
            ),
            "sources": [],
            "backend": "mock",
        }

    top_source = sources[0]
    if top_source["topic"] == "ram":
        answer = (
            "Com base na fonte recuperada, o Lenovo LOQ suporta até 32 GB de memória DDR5. "
            "Essa resposta deve ser confirmada com o manual final indexado pelo grupo."
        )
    elif top_source["topic"] == "undervolt":
        answer = (
            "A fonte de fórum recuperada cita um undervolt estável com CPU offset de -120 mV "
            "e GPU offset de -100 mV. Como vem de fórum, trate como referência prática, não como "
            "recomendação oficial do fabricante."
        )
    elif top_source["topic"] == "elden_ring":
        answer = (
            "A fonte de driver indica correção de stuttering em Elden Ring ao usar DLSS. "
            "Para uma resposta final, o RAG deve combinar esse trecho com notas de driver e relatos "
            "do dispositivo selecionado."
        )
    else:
        answer = (
            "Encontrei fontes relacionadas à pergunta. A resposta final ainda está em modo simulado; "
            "quando o backend do grupo estiver pronto, este ponto chamará o Qwen2.5:7B com os chunks "
            "mais relevantes e retornará as citações."
        )

    return {
        "answer": answer,
        "sources": sources,
        "backend": "mock",
    }
