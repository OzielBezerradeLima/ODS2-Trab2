import os
import itertools
import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ingestion.ingestion import load_raw_documents

# 1. DEFINIÇÃO DA GRADE DE HIPERPARÂMETROS
PARAMS_GRID = {
    "chunk_size": [400, 600, 800],
    "chunk_overlap": [50, 100],
    "embedding_model": [
        "all-MiniLM-L6-v2", # Mais rápido, focado em inglês
        "paraphrase-multilingual-MiniLM-L12-v2" # Mais pesado, suporta português
    ],
    "llm_model": [
        "qwen2.5:7b",
        "llama3:8b"
    ]
}

# 2. DEFINIÇÃO DO CONJUNTO DE TESTES (Perguntas vs Fonte Esperada)
# Ajuste as fontes esperadas de acordo com os nomes dos seus metadados reais
EVALUATION_SET = [
    {
        "question": "Qual é a capacidade máxima de RAM suportada pelo Acer Nitro?",
        "expected_source": "NITROV16SAI.pdf"
    },
    {
        "question": "Como resolver o problema de stuttering no ASUS?",
        "expected_source": "asus_stuttering.md"
    },
    {
        "question": "Como fazer undervolt no processador usando o Lenovo Vantage?",
        "expected_source": "guide_to_undervolting_cpu_with_lenovo_vantage_app.md"
    },
    {
        "question": "O que há de novo no Adrenalin Edition 24.3.1?",
        "expected_source": "AMD Software_ Adrenalin Edition 24.3.1 Release Notes.pdf"
    }
]

def run_grid_search():
    print("📥 Carregando documentos brutos (apenas uma vez)...")
    raw_docs = load_raw_documents()
    
    if not raw_docs:
        print("Nenhum documento encontrado. Verifique a pasta data/raw.")
        return

    # Gera todas as combinações possíveis de hiperparâmetros
    keys, values = zip(*PARAMS_GRID.items())
    experiments = [dict(zip(keys, v)) for v in itertools.product(*values)]
    
    print(f"🔬 Iniciando bateria de testes: {len(experiments)} combinações.")
    print("-" * 60)
    
    results_log = []

    for i, exp in enumerate(experiments, 1):
        c_size = exp["chunk_size"]
        c_overlap = exp["chunk_overlap"]
        model_name = exp["embedding_model"]
        
        print(f"Executando Teste {i}/{len(experiments)} | "
              f"Model: {model_name} | Size: {c_size} | Overlap: {c_overlap}")
        
        # A. Divisão do Texto
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=c_size,
            chunk_overlap=c_overlap,
            separators=["\n\n", "\n", " ", ""],
            length_function=len
        )
        chunks = text_splitter.split_documents(raw_docs)
        
        # B. Criação do Banco Vetorial Temporário (Em Memória)
        # Importante: EphemeralClient não salva no disco e limpa após o fim do teste
        temp_client = chromadb.EphemeralClient()
        emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)
        
        collection = temp_client.create_collection(
            name=f"test_col_{i}",
            embedding_function=emb_fn
        )
        
        # Prepara a ingestão
        docs_text = [c.page_content for c in chunks]
        metadatas = [c.metadata for c in chunks]
        ids = [f"id_{j}" for j in range(len(chunks))]
        
        collection.add(documents=docs_text, metadatas=metadatas, ids=ids)
        
        # C. Avaliação do Conjunto de Testes (Hit Rate @ 3)
        hits = 0
        
        for test in EVALUATION_SET:
            query = test["question"]
            expected = test["expected_source"]
            
            # Busca os 3 pedaços mais relevantes
            search_results = collection.query(
                query_texts=[query],
                n_results=3,
                include=["metadatas"]
            )
            
            # Verifica se o documento correto está entre os Top 3 recuperados
            retrieved_sources = [
                meta.get("source_file", meta.get("source", "")) 
                for meta in search_results["metadatas"][0]
            ]
            
            if expected in retrieved_sources:
                hits += 1

            # D. TESTE DE GERAÇÃO COM LLM
            print(f"\n--- Testando Pergunta: '{query}' com {exp['llm_model']} ---")
            
            # Monta o contexto juntando os textos recuperados
            contexto_recuperado = "\n\n".join(search_results["documents"][0])
            
            prompt = f"""
            {SYSTEM_PROMPT}

            CONTEXTO:
            {contexto_recuperado}

            PERGUNTA:
            {query}
            """
            
            try:
                # Chama o LLM passando o nome do modelo
                resposta_llm = generate(prompt, model_name=exp["llm_model"])
                print(f"🤖 Resposta do {exp['llm_model']}:\n{resposta_llm.strip()[:200]}...\n")
            except Exception as e:
                print(f"❌ Erro ao gerar com {exp['llm_model']}: {e}\n")
            # ==========================================

        accuracy = (hits / len(EVALUATION_SET)) * 100
        print(f"✅ Precisão de Recuperação: {accuracy:.2f}% ({hits}/{len(EVALUATION_SET)} acertos)\n")
        
        results_log.append({
            "config": exp,
            "accuracy": accuracy
        })
        
        # Limpa da memória antes do próximo teste
        temp_client.delete_collection(f"test_col_{i}")

    # 3. EXIBIÇÃO DO MELHOR MODELO
    best_run = max(results_log, key=lambda x: x["accuracy"])
    print("=" * 60)
    print("🏆 MELHOR CONFIGURAÇÃO ENCONTRADA:")
    print(f"Modelo de Embedding: {best_run['config']['embedding_model']}")
    print(f"Chunk Size: {best_run['config']['chunk_size']}")
    print(f"Chunk Overlap: {best_run['config']['chunk_overlap']}")
    print(f"Hit Rate @ 3: {best_run['accuracy']:.2f}%")
    print("=" * 60)

if __name__ == "__main__":
    # Desativa telemetria para os testes
    os.environ["ANONYMIZED_TELEMETRY"] = "False"
    run_grid_search()