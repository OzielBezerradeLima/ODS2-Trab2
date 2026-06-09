import { useMemo, useState } from "react";
import {
  Bot,
  Check,
  ClipboardCheck,
  Copy,
  Cpu,
  Download,
  FileText,
  Gamepad2,
  Laptop,
  Loader2,
  MessageSquare,
  RotateCcw,
  Search,
  Send,
  SlidersHorizontal,
  Table2,
  Trash2
} from "lucide-react";

import { askQuestion } from "./services/ragApi";

const deviceOptions = [
  { label: "Todos", value: "all" },
  { label: "Lenovo LOQ", value: "lenovo_loq" },
  { label: "Acer Nitro", value: "acer_nitro" },
  { label: "Asus TUF", value: "asus_tuf" }
];

const gameOptions = [
  { label: "Todos", value: "all" },
  { label: "Elden Ring", value: "elden_ring" },
  { label: "Cyberpunk 2077", value: "cyberpunk_2077" },
  { label: "Valorant", value: "valorant" },
  { label: "Forza Horizon", value: "forza_horizon" }
];

const starterQuestions = [
  "Qual o limite de RAM do LOQ?",
  "Houve correção de stuttering em Elden Ring?",
  "Melhor undervolt para Elden Ring?"
];

const documentTypeLabels = {
  manual: "Manual",
  driver_notes: "Driver Notes",
  forum: "Fórum"
};

const deviceLabels = {
  all: "Todos",
  generic: "Geral",
  lenovo_loq: "Lenovo LOQ",
  acer_nitro: "Acer Nitro",
  asus_tuf: "Asus TUF"
};

const topicLabels = {
  ram: "RAM",
  elden_ring: "Elden Ring",
  undervolt: "Undervolt",
  drivers: "Drivers",
  performance: "Desempenho"
};

const answeredOptions = ["Sim", "Parcial", "Não"];
const sourceOptions = ["Sim", "Não"];

function App() {
  const [activeView, setActiveView] = useState("chat");
  const [device, setDevice] = useState("all");
  const [game, setGame] = useState("all");
  const [topK, setTopK] = useState(5);
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [copiedMessageId, setCopiedMessageId] = useState("");

  const selectedLabels = useMemo(() => {
    return {
      device: deviceOptions.find((option) => option.value === device)?.label ?? "Todos",
      game: gameOptions.find((option) => option.value === game)?.label ?? "Todos"
    };
  }, [device, game]);

  async function handleSubmit(event) {
    event?.preventDefault();
    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || isLoading) {
      return;
    }

    const userMessage = {
      id: createId("question"),
      role: "user",
      content: trimmedQuestion
    };

    setError("");
    setQuestion("");
    setIsLoading(true);
    setActiveView("chat");
    setMessages((current) => [...current, userMessage]);

    try {
      const result = await askQuestion({
        question: trimmedQuestion,
        device,
        game,
        topK
      });

      const responseId = createId("answer");
      const evaluation = createEmptyEvaluation();
      const assistantMessage = {
        id: responseId,
        role: "assistant",
        question: trimmedQuestion,
        content: result.answer,
        sources: result.sources ?? [],
        backend: result.backend ?? "api",
        evaluation
      };

      setMessages((current) => [...current, assistantMessage]);
      setHistory((current) => [
        ...current,
        {
          id: responseId,
          time: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
          question: trimmedQuestion,
          answer: result.answer,
          device,
          game,
          sources: result.sources ?? [],
          evaluation
        }
      ]);
    } catch (err) {
      setError(err.message);
      setMessages((current) => [
        ...current,
        {
          id: createId("error"),
          role: "assistant",
          question: trimmedQuestion,
          content: "Não consegui consultar o backend agora. Verifique se a API RAG está ativa ou use o modo mock local.",
          sources: [],
          evaluation: createEmptyEvaluation()
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  function resetConversation() {
    setMessages([]);
    setHistory([]);
    setError("");
    setCopiedMessageId("");
  }

  function updateEvaluation(messageId, patch) {
    setMessages((current) =>
      current.map((message) => {
        if (message.id !== messageId) {
          return message;
        }

        return {
          ...message,
          evaluation: {
            ...createEmptyEvaluation(),
            ...message.evaluation,
            ...patch
          }
        };
      })
    );

    setHistory((current) =>
      current.map((item) => {
        if (item.id !== messageId) {
          return item;
        }

        return {
          ...item,
          evaluation: {
            ...createEmptyEvaluation(),
            ...item.evaluation,
            ...patch
          }
        };
      })
    );
  }

  function exportHistory() {
    const blob = new Blob([JSON.stringify(history, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "gearmind_historico_consultas.json";
    link.click();
    URL.revokeObjectURL(url);
  }

  async function copyAnswer(message) {
    const text = buildCopyText(message);

    try {
      await navigator.clipboard.writeText(text);
    } catch {
      fallbackCopy(text);
    }

    setCopiedMessageId(message.id);
    window.setTimeout(() => setCopiedMessageId(""), 1400);
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">GM</div>
          <div>
            <h1>GearMind</h1>
            <span>RAG Wiki</span>
          </div>
        </div>

        <section className="panel">
          <div className="panel-title">
            <SlidersHorizontal size={17} aria-hidden="true" />
            <span>Filtros</span>
          </div>

          <label className="field">
            <span>
              <Laptop size={16} aria-hidden="true" />
              Notebook
            </span>
            <select value={device} onChange={(event) => setDevice(event.target.value)}>
              {deviceOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>
              <Gamepad2 size={16} aria-hidden="true" />
              Jogo
            </span>
            <select value={game} onChange={(event) => setGame(event.target.value)}>
              {gameOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>
              <FileText size={16} aria-hidden="true" />
              Fontes
            </span>
            <input
              type="range"
              min="2"
              max="8"
              value={topK}
              onChange={(event) => setTopK(Number(event.target.value))}
            />
            <strong>{topK}</strong>
          </label>
        </section>

        <section className="panel history-panel">
          <div className="panel-title">
            <MessageSquare size={17} aria-hidden="true" />
            <span>Histórico</span>
          </div>

          {history.length === 0 ? (
            <p className="muted">Nenhuma consulta registrada.</p>
          ) : (
            <div className="history-list">
              {history.slice(-6).reverse().map((item, index) => (
                <article className="history-item" key={`${item.time}-${index}`}>
                  <time>{item.time}</time>
                  <p>{item.question}</p>
                </article>
              ))}
            </div>
          )}

          <div className="sidebar-actions">
            <button className="icon-button" type="button" title="Exportar histórico" onClick={exportHistory} disabled={!history.length}>
              <Download size={18} aria-hidden="true" />
            </button>
            <button className="icon-button" type="button" title="Limpar conversa" onClick={resetConversation}>
              <Trash2 size={18} aria-hidden="true" />
            </button>
          </div>
        </section>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Notebook: {selectedLabels.device} | Jogo: {selectedLabels.game}</p>
            <h2>{activeView === "chat" ? "Consulta técnica" : "Avaliação manual"}</h2>
          </div>

          <div className="topbar-actions">
            <div className="view-switch" aria-label="Alternar visualização">
              <button
                type="button"
                className={activeView === "chat" ? "active" : ""}
                onClick={() => setActiveView("chat")}
              >
                <MessageSquare size={16} aria-hidden="true" />
                Chat
              </button>
              <button
                type="button"
                className={activeView === "evaluation" ? "active" : ""}
                onClick={() => setActiveView("evaluation")}
              >
                <Table2 size={16} aria-hidden="true" />
                Avaliação
              </button>
            </div>

            <div className="status-pill">
              <Cpu size={16} aria-hidden="true" />
              Qwen2.5:7B
            </div>
          </div>
        </header>

        {activeView === "chat" ? (
          <>
            <section className="chat-surface" aria-live="polite">
              {messages.length === 0 ? (
                <div className="empty-state">
                  <Bot size={34} aria-hidden="true" />
                  <h3>Faça uma consulta</h3>
                  <div className="quick-grid">
                    {starterQuestions.map((starter) => (
                      <button
                        key={starter}
                        type="button"
                        className="quick-question"
                        onClick={() => setQuestion(starter)}
                      >
                        <Search size={15} aria-hidden="true" />
                        {starter}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="message-list">
                  {messages.map((message) => (
                    <Message
                      key={message.id}
                      message={message}
                      copied={copiedMessageId === message.id}
                      onCopy={copyAnswer}
                      onUpdateEvaluation={updateEvaluation}
                    />
                  ))}
                  {isLoading && (
                    <div className="message assistant">
                      <div className="avatar">
                        <Loader2 className="spin" size={17} aria-hidden="true" />
                      </div>
                      <div className="bubble">Buscando fontes e preparando resposta...</div>
                    </div>
                  )}
                </div>
              )}
            </section>

            {error && <p className="error-line">{error}</p>}

            <form className="composer" onSubmit={handleSubmit}>
              <button className="icon-button" type="button" title="Nova conversa" onClick={resetConversation}>
                <RotateCcw size={18} aria-hidden="true" />
              </button>
              <input
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Pergunte sobre RAM, drivers, stuttering, undervolt ou compatibilidade"
                aria-label="Pergunta"
              />
              <button className="send-button" type="submit" disabled={!question.trim() || isLoading} title="Enviar pergunta">
                <Send size={18} aria-hidden="true" />
                <span>Enviar</span>
              </button>
            </form>
          </>
        ) : (
          <EvaluationView
            history={history}
            onExport={exportHistory}
            onUpdateEvaluation={updateEvaluation}
          />
        )}
      </section>
    </main>
  );
}

function Message({ message, copied, onCopy, onUpdateEvaluation }) {
  const isAssistant = message.role === "assistant";

  return (
    <article className={`message ${message.role}`}>
      <div className="avatar">{isAssistant ? <Bot size={17} aria-hidden="true" /> : "EU"}</div>
      <div className="message-body">
        <div className="bubble">{message.content}</div>
        {isAssistant && (
          <>
            <div className="message-actions">
              <button className="text-button" type="button" onClick={() => onCopy(message)}>
                {copied ? <ClipboardCheck size={16} aria-hidden="true" /> : <Copy size={16} aria-hidden="true" />}
                {copied ? "Copiado" : "Copiar com fontes"}
              </button>
            </div>

            {message.sources?.length > 0 && (
              <div className="sources">
                {message.sources.map((source, index) => (
                  <SourceCard source={source} index={index} key={`${source.id}-${index}`} />
                ))}
              </div>
            )}

            <EvaluationControls
              evaluation={message.evaluation ?? createEmptyEvaluation()}
              onChange={(patch) => onUpdateEvaluation(message.id, patch)}
            />
          </>
        )}
      </div>
    </article>
  );
}

function SourceCard({ source, index }) {
  return (
    <article className="source-card">
      <div>
        <strong>{index + 1}. {source.source}</strong>
        <div className="badge-row">
          {getSourceBadges(source).map((badge) => (
            <span className={`badge ${badge.variant}`} key={badge.label}>
              {badge.label}
            </span>
          ))}
        </div>
        <span>Página {source.page} | {topicLabels[source.topic] ?? source.topic}</span>
      </div>
      {typeof source.score === "number" && <small>{source.score.toFixed(2)}</small>}
      <p>{source.content}</p>
    </article>
  );
}

function EvaluationControls({ evaluation, onChange }) {
  return (
    <section className="evaluation-box" aria-label="Avaliação da resposta">
      <div className="evaluation-row">
        <span>Respondeu?</span>
        <div className="choice-group">
          {answeredOptions.map((option) => (
            <button
              type="button"
              className={evaluation.answered === option ? "active" : ""}
              onClick={() => onChange({ answered: option })}
              key={option}
            >
              {option}
            </button>
          ))}
        </div>
      </div>

      <div className="evaluation-row">
        <span>Fonte correta?</span>
        <div className="choice-group">
          {sourceOptions.map((option) => (
            <button
              type="button"
              className={evaluation.sourceCorrect === option ? "active" : ""}
              onClick={() => onChange({ sourceCorrect: option })}
              key={option}
            >
              {option}
            </button>
          ))}
        </div>
      </div>

      <label className="notes-field">
        <span>Observações</span>
        <input
          value={evaluation.notes}
          onChange={(event) => onChange({ notes: event.target.value })}
          placeholder="Ex.: resposta parcial, fonte de fórum, falta manual oficial"
        />
      </label>
    </section>
  );
}

function EvaluationView({ history, onExport, onUpdateEvaluation }) {
  return (
    <section className="evaluation-view">
      <div className="evaluation-header">
        <div>
          <h3>Relatório de avaliação</h3>
          <p>{history.length} consulta{history.length === 1 ? "" : "s"} registrada{history.length === 1 ? "" : "s"}</p>
        </div>
        <button className="text-button" type="button" onClick={onExport} disabled={!history.length}>
          <Download size={16} aria-hidden="true" />
          Exportar JSON
        </button>
      </div>

      {history.length === 0 ? (
        <div className="table-empty">
          <Table2 size={30} aria-hidden="true" />
          <p>Nenhuma consulta avaliada ainda.</p>
        </div>
      ) : (
        <div className="evaluation-table-wrap">
          <table className="evaluation-table">
            <thead>
              <tr>
                <th>Pergunta</th>
                <th>Respondeu?</th>
                <th>Fonte correta?</th>
                <th>Fontes</th>
                <th>Observações</th>
              </tr>
            </thead>
            <tbody>
              {history.map((item) => (
                <tr key={item.id}>
                  <td>
                    <strong>{item.question}</strong>
                    <span>{deviceLabels[item.device] ?? item.device} | {gameLabel(item.game)}</span>
                  </td>
                  <td>
                    <select
                      value={item.evaluation?.answered ?? ""}
                      onChange={(event) => onUpdateEvaluation(item.id, { answered: event.target.value })}
                    >
                      <option value="">Selecionar</option>
                      {answeredOptions.map((option) => (
                        <option value={option} key={option}>{option}</option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <select
                      value={item.evaluation?.sourceCorrect ?? ""}
                      onChange={(event) => onUpdateEvaluation(item.id, { sourceCorrect: event.target.value })}
                    >
                      <option value="">Selecionar</option>
                      {sourceOptions.map((option) => (
                        <option value={option} key={option}>{option}</option>
                      ))}
                    </select>
                  </td>
                  <td>{item.sources?.length ?? 0}</td>
                  <td>
                    <input
                      value={item.evaluation?.notes ?? ""}
                      onChange={(event) => onUpdateEvaluation(item.id, { notes: event.target.value })}
                      placeholder="Observação"
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function getSourceBadges(source) {
  const badges = [
    {
      label: documentTypeLabels[source.document_type] ?? source.document_type ?? "Documento",
      variant: source.document_type === "forum" ? "forum" : source.document_type === "driver_notes" ? "driver" : "manual"
    },
    {
      label: deviceLabels[source.device] ?? source.device ?? "Geral",
      variant: "device"
    }
  ];

  if (typeof source.score === "number") {
    badges.push({
      label: similarityLabel(source.score),
      variant: source.score >= 0.7 ? "strong" : source.score >= 0.35 ? "medium" : "low"
    });
  }

  return badges;
}

function similarityLabel(score) {
  if (score >= 0.7) {
    return "Alta similaridade";
  }
  if (score >= 0.35) {
    return "Média similaridade";
  }
  return "Baixa similaridade";
}

function gameLabel(value) {
  return gameOptions.find((option) => option.value === value)?.label ?? value;
}

function createEmptyEvaluation() {
  return {
    answered: "",
    sourceCorrect: "",
    notes: ""
  };
}

function createId(prefix) {
  if (window.crypto?.randomUUID) {
    return `${prefix}_${window.crypto.randomUUID()}`;
  }

  return `${prefix}_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

function buildCopyText(message) {
  const lines = [message.content.trim()];

  if (message.sources?.length) {
    lines.push("", "Fontes:");
    message.sources.forEach((source, index) => {
      const page = source.page ? `, página ${source.page}` : "";
      const score = typeof source.score === "number" ? `, similaridade ${source.score.toFixed(2)}` : "";
      lines.push(`${index + 1}. ${source.source}${page} - ${documentTypeLabels[source.document_type] ?? source.document_type}${score}`);
    });
  }

  return lines.join("\n");
}

function fallbackCopy(text) {
  const textArea = document.createElement("textarea");
  textArea.value = text;
  textArea.setAttribute("readonly", "");
  textArea.style.position = "fixed";
  textArea.style.left = "-9999px";
  document.body.appendChild(textArea);
  textArea.select();
  document.execCommand("copy");
  document.body.removeChild(textArea);
}

export default App;
