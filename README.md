# GearMind RAG / LLM Wiki

Sistema RAG para consulta tecnica sobre notebooks gamer, drivers, jogos,
compatibilidade e otimizacao de desempenho.

## Arquitetura

```text
data/raw
  -> ingestion/ingestion.py
  -> ingestion/vector_store.py
  -> data/vector_store
  -> src/vector_search.py
  -> src/rag.py
  -> api.py
  -> frontend/
```

O backend usa ChromaDB para recuperacao semantica e Ollama com
`qwen2.5:7b` para gerar respostas com base nos trechos recuperados.

## Requisitos

- Python 3.11+
- Node.js 20+
- Ollama instalado e em execucao
- Modelo `qwen2.5:7b` baixado no Ollama
- No Linux, tenha tambem `python3-venv` e `python3-pip` instalados

## Instalacao do Backend

### Windows

Na raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Linux

Em distribuicoes baseadas em Debian/Ubuntu:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip nodejs npm
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Baixe o modelo usado pelo projeto em qualquer sistema:

```bash
ollama pull qwen2.5:7b
```

## Gerar Banco Vetorial

Depois de instalar as dependencias:

```bash
python -m ingestion.vector_store
```

Esse comando le os arquivos em `data/raw`, gera chunks e cria o banco em
`data/vector_store`.

## Rodar API RAG

Com o ambiente virtual ativado:

```bash
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Endpoints principais:

```text
GET  /health
POST /ask
```

Exemplo de corpo para `POST /ask`:

```json
{
  "question": "Qual o limite de RAM do LOQ?",
  "device": "lenovo_loq",
  "game": "all",
  "top_k": 5
}
```

## Rodar Frontend React

Em outro terminal:

### Windows

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

### Linux

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Abra o endereco indicado pelo Vite, normalmente:

```text
http://127.0.0.1:5173
```

O arquivo `frontend/.env` deve conter:

```text
VITE_RAG_API_URL=http://127.0.0.1:8000
```

Sem essa variavel, o frontend usa o mock local.

## Execucao Completa

Ordem recomendada para inicializar o projeto:

1. Criar e ativar o ambiente virtual.
2. Instalar as dependencias do backend.
3. Baixar o modelo no Ollama.
4. Gerar o banco vetorial com `python -m ingestion.vector_store`.
5. Iniciar a API com `uvicorn api:app --reload --host 127.0.0.1 --port 8000`.
6. Iniciar o frontend com `npm run dev` dentro da pasta `frontend`.

Se estiver no Linux e o comando `python` nao existir no ambiente virtual, use `python3`.

## Funcionalidades do Frontend

- Sidebar para selecionar notebook.
- Sidebar para selecionar jogo.
- Chat principal.
- Exibicao de fontes utilizadas.
- Badges por tipo de fonte, dispositivo e similaridade.
- Historico de consultas.
- Exportacao do historico em JSON.
- Avaliacao manual por resposta.
- Aba de relatorio de avaliacao.
- Copiar resposta com fontes.

## Tecnologias

- Python
- FastAPI
- ChromaDB
- Sentence Transformers
- Ollama
- Qwen2.5:7B
- React
- Vite
- Lucide React

## Limitacoes

- A qualidade das respostas depende da qualidade dos chunks indexados.
- Se `data/vector_store` ainda nao existir, a API responde sem contexto.
- Se o Ollama nao estiver rodando, a API retorna as fontes recuperadas e informa o erro.
- Perguntas fora da base devem ser recusadas.

## Divisao de Tarefas

### Integrante 1 - Engenharia de Dados / RAG

Responsavel pela coleta, ingestao, chunking, embeddings e banco vetorial.

### Integrante 2 - LLM e Inteligencia

Responsavel pela integracao com Ollama, prompt principal, respostas e citacoes.

### Integrante 3 - Frontend, Testes e Documentacao

Responsavel pelo frontend React, historico, fontes, avaliacao manual e README.
