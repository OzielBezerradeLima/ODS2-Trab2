from .llm import generate
from .prompts import SYSTEM_PROMPT
from .vector_search import search


SIMILARITY_THRESHOLD = 0.75

def has_relevant_context(results):

    if len(results) == 0:
        return False

    best_score = results[0]["score"]

    return best_score >= SIMILARITY_THRESHOLD


def build_context(results):

    context = ""

    for doc in results:

        context += f"""

DOCUMENTO:
{doc['source']}

PÁGINA:
{doc['page']}

TIPO:
{doc['document_type']}

CONTEÚDO:
{doc['content']}

--------------------------------------
"""

    return context


def answer_question(question):

    results = search(question)

    if not has_relevant_context(results):

        return """
Não encontrei essa informação na base de conhecimento disponível.

A GearMind é especializada em:

- Hardware
- Notebooks gamers
- Drivers
- Benchmarks
- Compatibilidade de RAM
- Compatibilidade de SSD
- Otimização de jogos
"""

    context = build_context(results)

    prompt = f"""
{SYSTEM_PROMPT}

CONTEXTO:

{context}

PERGUNTA:

{question}
"""

    return generate(prompt)