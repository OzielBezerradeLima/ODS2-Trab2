from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.rag import answer_question_detailed


app = FastAPI(
    title="GearMind RAG API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    device: str = "all"
    game: str = "all"
    top_k: int = Field(default=5, ge=1, le=10)


class Source(BaseModel):
    source: str
    page: int
    device: str
    document_type: str
    topic: str
    content: str
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    backend: str


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    return answer_question_detailed(
        question=question,
        device=payload.device,
        game=payload.game,
        top_k=payload.top_k,
    )
