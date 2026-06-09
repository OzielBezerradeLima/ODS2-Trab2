import os
import chromadb

os.environ["ANONYMIZED_TELEMETRY"] = "False"
CHROMA_PATH = os.path.join("data", "vector_store") 

client = chromadb.PersistentClient(
    path=CHROMA_PATH
)

collection = client.get_collection(
    "hardware_optimization_knowledge"
)

def search(question, filter_dict=None):

    results = collection.query(
        query_texts=[question],
        n_results=3,
        where=filter_dict,
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    docs = []

    for doc, meta, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):

        docs.append(
            {
                "content": doc,
                "source": meta.get("source_file", meta.get("source", "Origem desconhecida")),
                "page": meta.get("page", 1),
                "document_type": meta.get("category", "Categoria desconhecida"),
                "score": 1 - distance
            }
        )

    return docs