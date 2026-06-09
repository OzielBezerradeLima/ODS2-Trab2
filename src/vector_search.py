import math
import os
import re
import unicodedata
from collections import Counter

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    chromadb = None
    embedding_functions = None


os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

CHROMA_PATH = os.path.join("data", "vector_store")
COLLECTION_NAME = "hardware_optimization_knowledge"

embedding_function = None

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
    "no",
    "na",
    "o",
    "os",
    "para",
    "qual",
    "que",
    "um",
    "uma",
}

SYNONYMS = {
    "ram": {"ram", "memoria", "memory", "ddr4", "ddr5", "gb", "supports", "suporta"},
    "memoria": {"ram", "memoria", "memory", "ddr4", "ddr5", "gb", "supports", "suporta"},
    "limite": {"limite", "maximo", "maximum", "supports", "suporta", "up"},
    "loq": {"loq", "lenovo"},
    "lenovo": {"loq", "lenovo"},
    "elden": {"elden", "ring", "dlss", "stuttering", "travamento"},
    "ring": {"elden", "ring", "dlss", "stuttering", "travamento"},
    "stuttering": {"stuttering", "travamento", "engasgo", "frametime"},
    "undervolt": {"undervolt", "offset", "mv", "voltagem"},
}


def get_client():
    if chromadb is None:
        return None
    return chromadb.PersistentClient(path=CHROMA_PATH)


def get_collection(with_embedding=True):
    client = get_client()
    if client is None:
        return None

    try:
        if not with_embedding:
            return client.get_collection(name=COLLECTION_NAME)

        if embedding_functions is None:
            return client.get_collection(name=COLLECTION_NAME)

        global embedding_function
        if embedding_function is None:
            embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )

        return client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_function,
        )
    except Exception:
        return None


def search(question, filter_dict=None, top_k=5, device="all", topic="all"):
    effective_device = device
    if device == "all":
        inferred_device = infer_device(question.lower())
        effective_device = inferred_device if inferred_device != "generic" else "all"

    inferred_topic = infer_topic(question.lower())
    if inferred_topic != "general":
        effective_topic = inferred_topic
    elif topic != "all":
        effective_topic = topic
    else:
        effective_topic = "all"

    vector_docs = vector_search(
        question,
        filter_dict=filter_dict,
        top_k=top_k,
        device=effective_device,
        topic=effective_topic,
    )
    if vector_docs and vector_docs[0]["score"] >= 0.2:
        return vector_docs[:top_k]

    lexical_docs = lexical_search(
        question,
        top_k=top_k,
        device=effective_device,
        topic=effective_topic,
    )
    if lexical_docs:
        return lexical_docs[:top_k]

    return vector_docs[:top_k]


def vector_search(question, filter_dict=None, top_k=5, device="all", topic="all"):
    collection = get_collection(with_embedding=True)
    if collection is None:
        return []

    try:
        results = collection.query(
            query_texts=[question],
            n_results=max(top_k, 5),
            where=filter_dict,
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        return []

    docs = []

    for doc, meta, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        normalized = normalize_metadata(meta, doc)

        docs.append(
            {
                "content": doc,
                "source": normalized["source"],
                "page": normalized["page"],
                "device": normalized["device"],
                "document_type": normalized["document_type"],
                "topic": normalized["topic"],
                "score": max(0, 1 - distance),
            }
        )

    filtered_docs = filter_results(docs, device=device, topic=topic)
    return filtered_docs[:top_k]


def lexical_search(question, top_k=5, device="all", topic="all"):
    collection = get_collection(with_embedding=False)
    if collection is None:
        return []

    try:
        data = collection.get(include=["documents", "metadatas"])
    except Exception:
        return []

    query_tokens = expand_tokens(tokenize(question))
    query_vector = Counter(query_tokens)
    docs = []

    for content, meta in zip(data.get("documents", []), data.get("metadatas", [])):
        normalized = normalize_metadata(meta, content)
        searchable = f"{content} {normalized['source']} {normalized['device']} {normalized['topic']}"
        doc_tokens = expand_tokens(tokenize(searchable))
        score = cosine_similarity(query_vector, Counter(doc_tokens))

        if device != "all" and normalized["device"] in {device, "generic"}:
            score += 0.08
        if topic != "all" and normalized["topic"] == topic:
            score += 0.08

        if score > 0:
            docs.append(
                {
                    "content": content,
                    "source": normalized["source"],
                    "page": normalized["page"],
                    "device": normalized["device"],
                    "document_type": normalized["document_type"],
                    "topic": normalized["topic"],
                    "score": min(score, 1.0),
                }
            )

    filtered_docs = filter_results(docs, device=device, topic=topic)
    return sorted(filtered_docs, key=lambda doc: doc["score"], reverse=True)[:top_k]


def filter_results(docs, device="all", topic="all"):
    filtered = docs

    if device and device != "all":
        device_matches = [
            doc for doc in filtered
            if doc["device"] in {device, "generic"}
        ]
        if device_matches:
            filtered = device_matches

    if topic and topic != "all":
        topic_matches = [
            doc for doc in filtered
            if doc["topic"] == topic
        ]
        filtered = topic_matches

    return filtered


def tokenize(text):
    normalized = strip_accents(text.lower())
    words = re.findall(r"[a-zA-Z0-9_]+", normalized)
    return [word for word in words if word not in STOPWORDS and len(word) > 1]


def expand_tokens(tokens):
    expanded = set(tokens)
    for token in tokens:
        expanded.update(SYNONYMS.get(token, set()))
    return list(expanded)


def cosine_similarity(left, right):
    common = set(left) & set(right)
    numerator = sum(left[word] * right[word] for word in common)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))

    if not left_norm or not right_norm:
        return 0

    return numerator / (left_norm * right_norm)


def strip_accents(text):
    return "".join(
        char for char in unicodedata.normalize("NFD", text)
        if unicodedata.category(char) != "Mn"
    )


def normalize_metadata(meta, content):
    source = meta.get("source_file") or meta.get("source") or "Origem desconhecida"
    source_path = str(meta.get("source", source)).lower()
    source_name = str(source).lower()
    searchable = f"{source_path} {source_name} {content}".lower()

    return {
        "source": source,
        "page": int(meta.get("page", 1) or 1),
        "device": infer_device(searchable),
        "document_type": infer_document_type(searchable, meta),
        "topic": infer_topic(searchable),
    }


def infer_device(text):
    normalized = strip_accents(text)
    tokens = set(tokenize(normalized))

    if "lenovo" in tokens or any(token.startswith("loq") for token in tokens):
        return "lenovo_loq"
    if "acer" in tokens or "nitro" in tokens:
        return "acer_nitro"
    if "asus" in tokens or "tuf" in tokens or "rog" in tokens or "zephyrus" in tokens:
        return "asus_tuf"
    return "generic"


def infer_document_type(text, meta):
    category = str(meta.get("category", "")).lower()
    if category in {"manual", "driver_notes", "forum"}:
        return category
    if "thread" in text or "reddit" in text or ".md" in text:
        return "forum"
    if "patch" in text or "driver" in text or "adrenalin" in text or "nvidia" in text:
        return "driver_notes"
    return "manual"


def infer_topic(text):
    normalized = strip_accents(text)
    tokens = set(tokenize(normalized))

    if tokens & {"undervolt", "offset", "mv"}:
        return "undervolt"
    if tokens & {"ram", "memory", "memoria", "ddr4", "ddr5"}:
        return "ram"
    if tokens & {"driver", "drivers", "bios", "nvidia", "amd"}:
        return "drivers"
    if tokens & {"stuttering", "performance", "temperatura", "desempenho"}:
        return "performance"
    if tokens & {"elden", "ring", "dlss"}:
        return "elden_ring"
    return "general"
