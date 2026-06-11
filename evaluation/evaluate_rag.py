from __future__ import annotations

import argparse
import csv
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


def normalize(text: str) -> str:
    text = text.lower()
    replacements = {
        "á": "a", "à": "a", "â": "a", "ã": "a",
        "é": "e", "ê": "e",
        "í": "i",
        "ó": "o", "ô": "o", "õ": "o",
        "ú": "u",
        "ç": "c",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", normalize(text))


def keyword_recall(answer: str, expected_keywords: list[str]) -> float:
    if not expected_keywords:
        return 1.0

    normalized_answer = normalize(answer)
    hits = sum(1 for keyword in expected_keywords if normalize(keyword) in normalized_answer)
    return hits / len(expected_keywords)


def source_hit_rate(sources: list[dict[str, Any]], expected_sources: list[str]) -> float:
    if not expected_sources:
        return 1.0

    source_text = normalize(" ".join(str(source.get("source", "")) for source in sources))
    hits = sum(1 for expected in expected_sources if normalize(expected) in source_text)
    return hits / len(expected_sources)


def lcs_length(a: list[str], b: list[str]) -> int:
    previous = [0] * (len(b) + 1)
    for token_a in a:
        current = [0]
        for index_b, token_b in enumerate(b, start=1):
            if token_a == token_b:
                current.append(previous[index_b - 1] + 1)
            else:
                current.append(max(previous[index_b], current[-1]))
        previous = current
    return previous[-1]


def rouge_l_f1(candidate: str, reference: str | None) -> float | None:
    if not reference:
        return None

    candidate_tokens = tokenize(candidate)
    reference_tokens = tokenize(reference)
    if not candidate_tokens or not reference_tokens:
        return 0.0

    lcs = lcs_length(candidate_tokens, reference_tokens)
    precision = lcs / len(candidate_tokens)
    recall = lcs / len(reference_tokens)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def has_refusal(answer: str) -> bool:
    normalized = normalize(answer)
    refusal_patterns = [
        "nao encontrei",
        "base de conhecimento",
        "informacao nao esta presente",
        "informacao insuficiente",
    ]
    return any(pattern in normalized for pattern in refusal_patterns)


def evaluate_item(api_url: str, item: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    response = requests.post(
        f"{api_url.rstrip('/')}/ask",
        json={
            "question": item["question"],
            "device": item.get("device", "all"),
            "game": item.get("game", "all"),
            "top_k": item.get("top_k", 5),
            "model_name": item.get("model_name"),
        },
        timeout=120,
    )
    latency_seconds = time.perf_counter() - started
    response.raise_for_status()
    payload = response.json()

    answer = payload.get("answer", "")
    sources = payload.get("sources", [])
    source_scores = [source.get("score", 0) for source in sources if isinstance(source.get("score", 0), (int, float))]
    should_answer = item.get("should_answer", True)
    refused = has_refusal(answer)

    return {
        "id": item.get("id", item["question"]),
        "question": item["question"],
        "answer": answer,
        "backend": payload.get("backend"),
        "fallback_used": bool(payload.get("fallback_used", False)),
        "model_attempts": payload.get("model_attempts", []),
        "latency_seconds": round(latency_seconds, 3),
        "sources_count": len(sources),
        "avg_source_score": round(sum(source_scores) / len(source_scores), 4) if source_scores else 0,
        "keyword_recall": round(keyword_recall(answer, item.get("expected_keywords", [])), 4),
        "source_hit_rate": round(source_hit_rate(sources, item.get("expected_sources", [])), 4),
        "rouge_l_f1": rouge_l_f1(answer, item.get("reference_answer")),
        "answer_completeness": 1.0 if len(answer.strip()) >= item.get("min_answer_chars", 60) else 0.0,
        "refusal_correct": 1.0 if (not should_answer and refused) or (should_answer and not refused) else 0.0,
        "sources": sources,
    }


def aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
    numeric_keys = [
        "latency_seconds",
        "sources_count",
        "avg_source_score",
        "keyword_recall",
        "source_hit_rate",
        "answer_completeness",
        "refusal_correct",
    ]
    summary: dict[str, Any] = {"total_questions": len(results)}
    for key in numeric_keys:
        summary[f"avg_{key}"] = round(sum(float(result[key]) for result in results) / len(results), 4) if results else 0

    rouge_values = [result["rouge_l_f1"] for result in results if result["rouge_l_f1"] is not None]
    summary["avg_rouge_l_f1"] = round(sum(rouge_values) / len(rouge_values), 4) if rouge_values else None
    summary["fallback_rate"] = round(sum(1 for result in results if result["fallback_used"]) / len(results), 4) if results else 0
    return summary


def save_csv(path: Path, results: list[dict[str, Any]]) -> None:
    columns = [
        "id", "question", "backend", "fallback_used", "latency_seconds",
        "sources_count", "avg_source_score", "keyword_recall", "source_hit_rate",
        "rouge_l_f1", "answer_completeness", "refusal_correct",
    ]
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=columns)
        writer.writeheader()
        for result in results:
            writer.writerow({column: result.get(column) for column in columns})


def main() -> None:
    parser = argparse.ArgumentParser(description="Avalia o RAG GearMind usando perguntas de teste.")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--dataset", default="evaluation/qa_dataset.json")
    parser.add_argument("--output-dir", default="evaluation/results")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    results = [evaluate_item(args.api_url, item) for item in dataset]
    summary = aggregate(results)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"rag_eval_{timestamp}.json"
    csv_path = output_dir / f"rag_eval_{timestamp}.csv"

    json_path.write_text(
        json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    save_csv(csv_path, results)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Resultados salvos em: {json_path}")
    print(f"Resumo CSV salvo em: {csv_path}")


if __name__ == "__main__":
    main()
