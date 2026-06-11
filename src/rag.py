import os
import re
from dataclasses import dataclass

from .llm import generate
from .prompts import SYSTEM_PROMPT
from .vector_search import search


SIMILARITY_THRESHOLD = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.2"))
MIN_ANSWER_CHARS = int(os.getenv("RAG_MIN_ANSWER_CHARS", "60"))
DEFAULT_MODEL_FALLBACKS = os.getenv(
    "RAG_MODEL_FALLBACKS",
    "qwen2.5:7b,qwen2.5:3b,qwen2.5:1.5b",
)

NO_CONTEXT_ANSWER = """
Nao encontrei essa informacao na base de conhecimento disponivel.

A GearMind e especializada em:

- Hardware
- Notebooks gamers
- Drivers
- Benchmarks
- Compatibilidade de RAM
- Compatibilidade de SSD
- Otimizacao de jogos
"""

WEAK_ANSWER_PATTERNS = [
    r"nao sei",
    r"não sei",
    r"nao encontrei",
    r"não encontrei",
    r"nao ha informacao",
    r"não há informação",
    r"nao tenho informacao",
    r"não tenho informação",
    r"informacao insuficiente",
    r"informação insuficiente",
]


@dataclass
class ModelAttempt:
    model: str
    status: str
    reason: str

    def to_dict(self):
        return {"model": self.model, "status": self.status, "reason": self.reason}


def get_model_chain(preferred_model: str | None = None) -> list[str]:
    models = [model.strip() for model in DEFAULT_MODEL_FALLBACKS.split(",") if model.strip()]

    if preferred_model:
        models = [preferred_model] + [model for model in models if model != preferred_model]

    return models or ["qwen2.5:7b"]


def has_relevant_context(results):
    if len(results) == 0:
        return False

    best_score = results[0]["score"]
    return best_score >= SIMILARITY_THRESHOLD


def build_context(results):
    context = ""

    for index, doc in enumerate(results, start=1):
        context += f"""

FONTE {index}:
Arquivo: {doc['source']}
Pagina: {doc['page']}
Tipo: {doc['document_type']}
Dispositivo: {doc.get('device', 'generic')}
Topico: {doc.get('topic', 'general')}
Similaridade: {doc.get('score', 0):.2f}

CONTEUDO:
{doc['content']}

--------------------------------------
"""

    return context


def answer_question(question):
    return answer_question_detailed(question)["answer"]


def answer_question_detailed(question, device="all", game="all", top_k=5, model_name=None):
    results = search(
        question,
        top_k=top_k,
        device=device,
        topic=game,
    )

    if not has_relevant_context(results):
        return {
            "answer": NO_CONTEXT_ANSWER.strip(),
            "sources": [],
            "backend": "rag",
            "fallback_used": False,
            "model_attempts": [],
        }

    context = build_context(results)

    prompt = f"""
{SYSTEM_PROMPT}

CONTEXTO:

{context}

PERGUNTA:

{question}
"""

    attempts = []
    model_chain = get_model_chain(model_name)

    for model in model_chain:
        try:
            raw_answer = generate(prompt, model_name=model)
            answer = format_answer(raw_answer, results)
            is_valid, reason = is_answer_acceptable(answer)

            if is_valid:
                attempts.append(ModelAttempt(model, "ok", reason))
                return {
                    "answer": answer,
                    "sources": serialize_sources(results),
                    "backend": model,
                    "fallback_used": len(attempts) > 1,
                    "model_attempts": [attempt.to_dict() for attempt in attempts],
                }

            attempts.append(ModelAttempt(model, "weak_answer", reason))
        except Exception as exc:
            attempts.append(ModelAttempt(model, "error", str(exc)))

    answer = build_fallback_answer(question, results, attempts)
    return {
        "answer": answer,
        "sources": serialize_sources(results),
        "backend": "extractive_fallback",
        "fallback_used": True,
        "model_attempts": [attempt.to_dict() for attempt in attempts],
    }


def serialize_sources(results):
    return [
        {
            "source": doc.get("source", "Origem desconhecida"),
            "page": doc.get("page", 1),
            "device": doc.get("device", "generic"),
            "document_type": doc.get("document_type", "manual"),
            "topic": doc.get("topic", "general"),
            "content": doc.get("content", ""),
            "score": doc.get("score", 0),
        }
        for doc in results
    ]


def format_answer(answer, results):
    text = answer.strip()
    text = re.sub(r"^\s*Resposta:\s*", "", text, flags=re.IGNORECASE)
    text = re.split(r"\n\s*Fontes?:\s*", text, flags=re.IGNORECASE)[0].strip()

    if not text:
        text = "Encontrei trechos relevantes na base, mas o modelo nao gerou uma resposta textual completa."

    return f"{text}\n\n{format_sources(results)}"


def is_answer_acceptable(answer: str) -> tuple[bool, str]:
    answer_text = answer.strip()
    answer_without_sources = re.split(r"\n\s*Fontes utilizadas:\s*", answer_text, flags=re.IGNORECASE)[0].strip()

    if len(answer_without_sources) < MIN_ANSWER_CHARS:
        return False, "resposta curta demais"

    normalized = normalize_text(answer_without_sources)
    if any(re.search(pattern, normalized) for pattern in WEAK_ANSWER_PATTERNS):
        return False, "resposta indica incerteza ou falta de informacao"

    return True, "resposta aceita"


def normalize_text(text: str) -> str:
    return text.lower().strip()


def format_sources(results):
    source_lines = []
    seen = set()

    for doc in results:
        key = (doc.get("source"), doc.get("page"))
        if key in seen:
            continue

        seen.add(key)
        source_lines.append(
            f"- {doc.get('source', 'Origem desconhecida')} - Pagina {doc.get('page', 1)}"
        )

    if not source_lines:
        return "Fontes utilizadas:\n- Nenhuma fonte recuperada."

    return "Fontes utilizadas:\n" + "\n".join(source_lines)


def build_fallback_answer(question, results, attempts):
    top_source = results[0]
    errors = "; ".join(
        f"{attempt.model}: {attempt.status} ({attempt.reason})" for attempt in attempts
    )
    answer = (
        "Encontrei trechos relevantes na base, mas nenhum modelo gerou uma resposta "
        "com qualidade suficiente. Pelo contexto recuperado, consulte principalmente "
        f"a fonte {top_source.get('source', 'desconhecida')}, pagina {top_source.get('page', 1)}. "
        f"Tentativas realizadas: {errors}"
    )

    return f"{answer}\n\n{format_sources(results)}"
