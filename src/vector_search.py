import chromadb

client = chromadb.PersistentClient(
    path="vectorstore"
)

collection = client.get_collection(
    "gearmind"
)

def search(question):

    results = collection.query(
        query_texts=[question],
        n_results=3,
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
                "source": meta["source"],
                "page": meta["page"],
                "document_type": meta["document_type"],
                "score": 1 - distance
            }
        )

    return docs