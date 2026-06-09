import { mockAskQuestion } from "./mockRag";

const apiUrl = import.meta.env.VITE_RAG_API_URL;

export async function askQuestion(payload) {
  if (!apiUrl) {
    await wait(350);
    return mockAskQuestion(payload);
  }

  const response = await fetch(`${apiUrl.replace(/\/$/, "")}/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      question: payload.question,
      device: payload.device,
      game: payload.game,
      top_k: payload.topK
    })
  });

  if (!response.ok) {
    throw new Error("Não foi possível consultar o backend RAG.");
  }

  return response.json();
}

function wait(ms) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}
