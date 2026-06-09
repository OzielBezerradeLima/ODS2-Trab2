import os
import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter
# Importamos as funções de ingestão criadas na Etapa 2
from ingestion.ingestion import load_raw_documents, split_documents

# ==============================================================================
# CONFIGURAÇÕES DE DIRETÓRIOS E BANCO VETORIAL
# ==============================================================================
CHROMA_DATA_DIR = os.path.join("data", "vector_store")
COLLECTION_NAME = "hardware_optimization_knowledge"

# ==============================================================================
# 1. CONFIGURAÇÃO DO MODELO DE EMBEDDINGS (Open-Source e Local)
# ==============================================================================
# Usamos o all-MiniLM-L6-v2 da HuggingFace, rodando localmente na máquina
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)

# ==============================================================================
# 2. INICIALIZAÇÃO E INDEXAÇÃO DO BANCO VETORIAL
# ==============================================================================
def build_vector_store():
    """
    Executa o pipeline da Etapa 2, inicializa o ChromaDB persistente
    e indexa todos os chunks gerados com seus respectivos metadados.
    """
    print("📦 Executando pipeline de dados (Carga + Chunking)...")
    raw_docs = load_raw_documents()
    if not raw_docs:
        print("⚠️ Nenhum documento bruto encontrado. Abortando criação do banco.")
        return None
        
    chunks = split_documents(raw_docs)
    
    print(f"🏢 Inicializando ChromaDB local em: {CHROMA_DATA_DIR}")
    # Cria o cliente persistente (salva os dados no disco rígido)
    chroma_client = chromadb.PersistentClient(path=CHROMA_DATA_DIR)
    
    # Cria ou obtém a coleção configurando a função de embedding open-source
    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function
    )
    
    print("📥 Indexando documentos no banco vetorial (gerando embeddings)...")
    
    # Preparando as estruturas exigidas pelo ChromaDB nativo
    documents_text = []
    metadatas = []
    ids = []
    
    for idx, chunk in enumerate(chunks):
        documents_text.append(chunk.page_content)
        metadatas.append(chunk.metadata)
        ids.append(f"id_chunk_{idx}")
        
    # Adiciona em lote no banco vetorial
    collection.add(
        documents=documents_text,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"🎉 Sucesso! {collection.count()} chunks indexados com sucesso no banco vetorial.")
    return collection

# ==============================================================================
# 3. IMPLEMENTAÇÃO DA FUNÇÃO DE BUSCA SEMÂNTICA (Exigida no Exemplo)
# ==============================================================================
def search(query: str, category_filter: str = None, top_k: int = 3):
    """
    Realiza a busca por similaridade semântica no banco de dados.
    Permite filtrar opcionalmente por metadados (categoria do hardware/fonte).
    """
    chroma_client = chromadb.PersistentClient(path=CHROMA_DATA_DIR)
    
    # Verifica se o banco existe antes de consultar
    try:
        collection = chroma_client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_function
        )
    except Exception:
        print("❌ Erro: O Banco Vetorial não foi construído. Execute o script como main primeiro.")
        return []
        
    # Configuração de filtros por metadados se fornecidos (Manual, Driver, Community)
    where_clause = {}
    if category_filter:
        where_clause = {"category": category_filter}
        
    # Executa a busca vetorial por proximidade de cosseno
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        where=where_clause if category_filter else None
    )
    
    # Formata o retorno para ficar limpo e fácil de consumir na interface/LLM
    formatted_results = []
    if results and results['documents']:
        for i in range(len(results['documents'][0])):
            formatted_results.append({
                "text": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i] if 'distances' in results else None
            })
            
    return formatted_results

# ==============================================================================
# SCRIPT DE INICIALIZAÇÃO / TESTE UNITÁRIO
# ==============================================================================
if __name__ == "__main__":
    print("🚀 Iniciando ETAPA 3 – Construindo Banco Vetorial...")
    
    # 1. Constroi e popula o banco
    build_vector_store()
    
    # 2. Teste rápido de fumaça (Smoke Test) para validar a busca semântica
    print("\n🔬 Testando a Função de Busca Semântica...")
    termo_de_teste = "Como resolver o stuttering no Valorant no notebook Asus TUF"
    
    print(f"Query de teste: '{termo_de_teste}'")
    resultados_busca = search(termo_de_teste, top_k=2)
    
    print("\n🔍 Resultados Encontrados no Banco:")
    for i, res in enumerate(resultados_busca):
        print(f"\n[Resultado {i+1}] - Distância Semântica: {res['distance']:.4f}")
        print(f"Fonte: {res['metadata']['source_file']} | Categoria: {res['metadata']['category']}")
        print(f"Trecho recuperado:\n{res['text']}")
        print("-" * 50)
