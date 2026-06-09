import re

from .llm import generate
from .prompts import SYSTEM_PROMPT
from .vector_search import search


SIMILARITY_THRESHOLD = 0.2

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


def answer_question_detailed(question, device="all", game="all", top_k=5, model_name="qwen2.5:7b"):
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
        }

    context = build_context(results)

    prompt = f"""
{SYSTEM_PROMPT}

CONTEXTO:

{context}

PERGUNTA:

{question}
"""

    try:
        answer = format_answer(generate(prompt, model_name=model_name), results)
        
        backend = model_name 
    except Exception as exc:
        answer = build_fallback_answer(question, results, exc)
        backend = "rag"

    return {
        "answer": answer,
        "sources": serialize_sources(results),
        "backend": backend,
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


def build_fallback_answer(question, results, error):
    top_source = results[0]
    answer = (
        "Encontrei trechos relevantes na base, mas nao foi possivel consultar o Qwen2.5:7B "
        "neste momento. Pelo contexto recuperado, a resposta deve ser analisada a partir "
        f"da fonte {top_source.get('source', 'desconhecida')}, pagina {top_source.get('page', 1)}. "
        f"Erro tecnico: {error}"
    )

    return f"{answer}\n\n{format_sources(results)}"
