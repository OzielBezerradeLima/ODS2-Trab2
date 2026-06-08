from .llm import generate
from .prompts import SYSTEM_PROMPT


SIMILARITY_THRESHOLD = 0.75


def search(question):

    """
    MOCK TEMPORÁRIO

    Substituir futuramente pela busca
    do ChromaDB.
    """

    if "ram" in question.lower():

        return [
            {
                "content": """
                O Lenovo LOQ suporta até
                32 GB DDR5.
                """,

                "source": "Manual Lenovo LOQ",

                "page": 14,

                "document_type": "manual",

                "score": 0.92
            },

            {
                "content": """
                Frequência máxima:
                4800 MHz.
                """,

                "source": "Manual Lenovo LOQ",

                "page": 15,

                "document_type": "manual",

                "score": 0.87
            }
        ]

    return []


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


def answer(question):

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