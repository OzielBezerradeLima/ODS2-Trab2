const mockChunks = [
  {
    id: "chunk_001",
    content: "Supports up to 32 GB DDR5 memory.",
    metadata: {
      source: "Lenovo LOQ User Guide",
      page: 14,
      device: "lenovo_loq",
      document_type: "manual",
      topic: "ram"
    }
  },
  {
    id: "chunk_102",
    content: "Fixed stuttering issues in Elden Ring when using DLSS.",
    metadata: {
      source: "NVIDIA Driver 555.85",
      page: 1,
      device: "generic",
      document_type: "driver_notes",
      topic: "elden_ring"
    }
  },
  {
    id: "chunk_245",
    content: "Stable undervolt: CPU offset -120mV. GPU offset -100mV.",
    metadata: {
      source: "Reddit r/LenovoLOQ",
      page: 1,
      device: "lenovo_loq",
      document_type: "forum",
      topic: "undervolt"
    }
  },
  {
    id: "chunk_310",
    content: "Acer Nitro models may require BIOS and GPU driver updates before testing performance issues.",
    metadata: {
      source: "Acer Nitro Support Notes",
      page: 3,
      device: "acer_nitro",
      document_type: "manual",
      topic: "drivers"
    }
  },
  {
    id: "chunk_411",
    content: "Asus TUF Gaming notebooks include performance profiles that affect fan speed, temperature and clock behavior.",
    metadata: {
      source: "Asus TUF Gaming User Guide",
      page: 22,
      device: "asus_tuf",
      document_type: "manual",
      topic: "performance"
    }
  }
];

const stopwords = new Set(["a", "ao", "as", "com", "da", "de", "do", "dos", "e", "em", "o", "os", "para", "qual", "que", "um", "uma"]);

const topicSynonyms = {
  ram: new Set(["ram", "memoria", "memory", "ddr5", "gb"]),
  undervolt: new Set(["undervolt", "offset", "mv", "voltagem", "temperatura"]),
  elden_ring: new Set(["elden", "ring", "dlss", "stuttering", "travamento", "engasgo"]),
  drivers: new Set(["driver", "drivers", "bios", "nvidia", "amd", "update"]),
  performance: new Set(["performance", "desempenho", "fan", "clock", "temperatura"])
};

const offTopicTerms = new Set(["bolo", "receita", "cozinha", "ingrediente", "assar"]);

function tokenize(text) {
  return text
    .toLowerCase()
    .match(/[a-zA-Z0-9_]+/g)
    ?.filter((word) => !stopwords.has(word) && word.length > 1) ?? [];
}

function cosineSimilarity(leftTokens, rightTokens) {
  const left = count(leftTokens);
  const right = count(rightTokens);
  const common = Object.keys(left).filter((word) => right[word]);
  const numerator = common.reduce((sum, word) => sum + left[word] * right[word], 0);
  const leftNorm = Math.sqrt(Object.values(left).reduce((sum, value) => sum + value * value, 0));
  const rightNorm = Math.sqrt(Object.values(right).reduce((sum, value) => sum + value * value, 0));

  if (!leftNorm || !rightNorm) {
    return 0;
  }

  return numerator / (leftNorm * rightNorm);
}

function count(tokens) {
  return tokens.reduce((acc, token) => {
    acc[token] = (acc[token] ?? 0) + 1;
    return acc;
  }, {});
}

function inferTopics(tokens) {
  const topics = new Set();
  Object.entries(topicSynonyms).forEach(([topic, synonyms]) => {
    if (tokens.some((token) => synonyms.has(token))) {
      topics.add(topic);
    }
  });
  return topics;
}

export function mockAskQuestion({ question, device = "all", game = "all", topK = 5 }) {
  const questionTokens = tokenize(question);
  const questionTokenSet = new Set(questionTokens);

  if ([...questionTokenSet].some((token) => offTopicTerms.has(token))) {
    return {
      answer: "Não encontrei informação suficiente nas fontes técnicas do projeto para responder essa pergunta. A base atual é voltada a notebooks gamer, drivers, jogos e ajustes de desempenho.",
      sources: [],
      backend: "mock"
    };
  }

  const inferredTopics = inferTopics(questionTokens);
  const sources = mockChunks
    .map((chunk) => {
      const metadata = chunk.metadata;
      const chunkText = `${chunk.content} ${metadata.source} ${metadata.topic} ${metadata.device}`;
      let score = cosineSimilarity(questionTokens, tokenize(chunkText));

      if (device !== "all" && [device, "generic"].includes(metadata.device)) {
        score += 0.12;
      }
      if (game !== "all" && metadata.topic === game) {
        score += 0.16;
      }
      if (inferredTopics.has(metadata.topic)) {
        score += 0.2;
      }

      return {
        id: chunk.id,
        content: chunk.content,
        score: Math.min(score, 1),
        ...metadata
      };
    })
    .filter((source) => source.score > 0)
    .sort((left, right) => right.score - left.score)
    .slice(0, topK);

  if (!sources.length) {
    return {
      answer: "Não encontrei trechos relevantes na base disponível. Quando o pipeline RAG completo for conectado, esta resposta deverá vir do Qwen2.5:7B usando apenas os chunks recuperados.",
      sources: [],
      backend: "mock"
    };
  }

  const topic = sources[0].topic;
  const answers = {
    ram: "Com base na fonte recuperada, o Lenovo LOQ suporta até 32 GB de memória DDR5. Essa resposta deve ser confirmada com o manual final indexado pelo grupo.",
    undervolt: "A fonte de fórum recuperada cita um undervolt estável com CPU offset de -120 mV e GPU offset de -100 mV. Como vem de fórum, trate como referência prática, não como recomendação oficial do fabricante.",
    elden_ring: "A fonte de driver indica correção de stuttering em Elden Ring ao usar DLSS. Para uma resposta final, o RAG deve combinar esse trecho com notas de driver e relatos do dispositivo selecionado.",
    drivers: "Encontrei fontes relacionadas a drivers e BIOS. Para problemas de desempenho, a resposta final deve priorizar patch notes oficiais e manuais do fabricante.",
    performance: "Encontrei fontes sobre perfis de desempenho, ventoinhas, temperatura e comportamento de clock. A resposta final deve citar o documento do modelo selecionado."
  };

  return {
    answer: answers[topic] ?? "Encontrei fontes relacionadas à pergunta. A resposta final ainda está em modo simulado; quando o backend do grupo estiver pronto, este ponto chamará o Qwen2.5:7B com os chunks mais relevantes e retornará as citações.",
    sources,
    backend: "mock"
  };
}
