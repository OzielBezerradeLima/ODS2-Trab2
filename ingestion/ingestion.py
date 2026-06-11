import os
import glob
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ==============================================================================
# CONFIGURAÇÕES DE DIRETÓRIOS
# ==============================================================================
RAW_DIR = os.path.join("data", "raw")
PROCESSED_DIR = os.path.join("data", "processed")

# Garante que as pastas existam
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# ==============================================================================
# 1. FUNÇÃO DE LIMPEZA TEXTUAL (Remoção de ruídos básicos)
# ==============================================================================
def clean_text(text: str) -> str:
    """
    Realiza a limpeza do texto extraído para evitar poluição nos embeddings.
    Remover quebras de linha excessivas e espaços em branco redundantes.
    """
    if not text:
        return ""
    # Substitui múltiplas quebras de linha ou espaços por um único espaço/quebra
    lines = [line.strip() for line in text.splitlines()]
    cleaned_lines = [line for line in lines if line] # Remove linhas vazias
    return "\n".join(cleaned_lines)

# ==============================================================================
# 2. PIPELINE DE INGESTÃO E CARREGAMENTO
# ==============================================================================
def load_raw_documents():
    """
    Varre a pasta data/raw/, identifica os formatos (PDF, MD, TXT),
    extrai o texto e injeta os metadados iniciais de origem.
    """
    documents = []
    
    # Procura por todos os arquivos recursivamente na pasta raw
    all_files = glob.glob(os.path.join(RAW_DIR, "**", "*.*"), recursive=True)
    
    print(f"🔍 Encontrados {len(all_files)} arquivos para processamento.")

    for file_path in all_files:
        file_name = os.path.basename(file_path)
        ext = os.path.splitext(file_name)[1].lower()
        
        # Mapeia a categoria com base na subpasta (manual, driver ou community)
        category = "generic"
        if "manual" in file_path.lower():
            category = "manual"
        elif "driver" in file_path.lower():
            category = "driver"
        elif "community" in file_path.lower():
            category = "community"

        try:
            if ext == ".pdf":
                loader = PyPDFLoader(file_path)
                loaded_docs = loader.load()
            elif ext == ".md":
                loader = TextLoader(file_path, encoding="utf-8")
                loaded_docs = loader.load()
            elif ext == ".txt":
                loader = TextLoader(file_path, encoding="utf-8")
                loaded_docs = loader.load()
            else:
                continue # Ignora formatos não mapeados
            
            # Aplica a limpeza textual e enriquece os metadados
            for doc in loaded_docs:
                doc.page_content = clean_text(doc.page_content)
                doc.metadata["source_file"] = file_name
                doc.metadata["category"] = category
                # Mantém o número da página se for PDF, senão define como 1
                if "page" not in doc.metadata:
                    doc.metadata["page"] = 1
                    
                documents.append(doc)
                
            print(f"✅ Processado com sucesso: {file_name} ({category})")
            
        except Exception as e:
            print(f"❌ Erro ao processar o arquivo {file_name}: {str(e)}")
            
    return documents

# ==============================================================================
# 3. ESTRATÉGIA DE CHUNKING (Divisão dos documentos)
# ==============================================================================
def split_documents(documents):
    """
    Aplica o RecursiveCharacterTextSplitter para dividir os textos.
    A estratégia usa separadores lógicos para tentar manter tabelas,
    tópicos e parágrafos de hardware sempre no mesmo bloco de contexto.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""],
        length_function=len
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"✂️ Documentos originais divididos em {len(chunks)} chunks menores.")
    return chunks

# ==============================================================================
# EXECUÇÃO PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    print("🚀 Iniciando ETAPA 2 – Ingestão e Chunking...")
    
    # 1. Carregar e limpar
    raw_docs = load_raw_documents()
    
    if not raw_docs:
        print("⚠️ Nenhum documento válido encontrado na pasta data/raw/. Abortando.")
        exit()
        
    # 2. Aplicar Chunking
    final_chunks = split_documents(raw_docs)
    
    # 3. Salvar uma prévia estruturada em data/processed para auditoria (Exigido no entregável)
    preview_path = os.path.join(PROCESSED_DIR, "chunks_preview.txt")
    with open(preview_path, "w", encoding="utf-8") as f:
        for i, chunk in enumerate(final_chunks):
            f.write(f"--- CHUNK {i} ---\n")
            f.write(f"METADADOS: {chunk.metadata}\n")
            f.write(f"CONTEÚDO:\n{chunk.page_content}\n\n")
            
    print(f"💾 Arquivo de auditoria gerado em: {preview_path}")
    print("🎉 Etapa 2 concluída com sucesso!")