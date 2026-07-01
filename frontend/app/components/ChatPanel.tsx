"use client";
import { useEffect, useRef, useState } from "react";
import type { CitationRef } from "@/app/lib/api";
import { queryDocuments } from "@/app/lib/api";
import MessageBubble, { type Message } from "./MessageBubble";

interface Props {
  scopedDocId: string | null;
  scopedDocName: string | null;
  onCitationClick: (citation: CitationRef) => void;
  onClearScope: () => void;
}

const QUERY_STAGES = ["Searching contracts…", "Reranking relevant passages…", "Drafting a cited answer…"];
const STAGE_MS = 650;

export default function ChatPanel({ scopedDocId, scopedDocName, onCitationClick, onClearScope }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [stageIndex, setStageIndex] = useState(-1);
  const bottomRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, stageIndex]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);
    setStageIndex(0);

    timerRef.current = setInterval(() => {
      setStageIndex((i) => (i < QUERY_STAGES.length - 1 ? i + 1 : i));
    }, STAGE_MS);

    // Wait for both the real response and the full staged sequence, so a fast
    // answer never truncates the narration and a slow one just holds the last
    // stage instead of desyncing from the actual request.
    const minimumSequence = new Promise<void>((resolve) => setTimeout(resolve, QUERY_STAGES.length * STAGE_MS));

    try {
      const [response] = await Promise.all([queryDocuments(question, scopedDocId), minimumSequence]);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.answer, response },
      ]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Something went wrong";
      const isRateLimit = msg.includes("rate_limit") || msg.includes("429") || msg.includes("per 1 hour");
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: isRateLimit
            ? "You've reached the query limit (20/hour). Please try again later."
            : `Error: ${msg}`,
          response: { answer: "", found: false, citations: [] },
        },
      ]);
    } finally {
      if (timerRef.current) clearInterval(timerRef.current);
      setLoading(false);
      setStageIndex(-1);
    }
  }

  const placeholder = scopedDocName
    ? `Ask about "${scopedDocName}"…`
    : "Ask a question about any of the contracts…";

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-hairline bg-surface">
        <h2 className="font-display italic text-ink">Chat with your contracts</h2>
      </div>

      {scopedDocName && (
        <div className="mx-4 mt-3 flex items-center justify-between gap-3 bg-highlight-soft border-l-4 border-citation rounded-r-md px-3 py-2 text-sm shadow-sm">
          <span className="text-ink">
            <span className="font-data text-[0.7rem] uppercase tracking-wide text-citation mr-1.5">Exhibit —</span>
            Searching within {scopedDocName}
          </span>
          <button
            onClick={onClearScope}
            className="shrink-0 flex items-center gap-1 border border-citation text-citation hover:bg-citation hover:text-white rounded px-2 py-1 text-xs transition-colors"
          >
            ✕ Clear
          </button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {messages.length === 0 && (
          <p className="text-sm text-ink-muted text-center mt-8">
            Ask a question about any of the preloaded contracts, or upload your own.
          </p>
        )}
        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} onCitationClick={onCitationClick} />
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-surface border border-hairline rounded-2xl rounded-tl-sm px-4 py-3 text-sm">
              <ol className="flex flex-col gap-1.5">
                {QUERY_STAGES.map((stage, i) => (
                  <li key={stage} className="flex items-center gap-2">
                    <span
                      className={`w-3.5 h-3.5 rounded-full border flex items-center justify-center shrink-0 ${
                        i < stageIndex
                          ? "bg-verified border-verified text-white"
                          : i === stageIndex
                            ? "border-citation animate-pulse"
                            : "border-hairline"
                      }`}
                      aria-hidden
                    >
                      {i < stageIndex && <span className="text-[0.5rem]">✓</span>}
                    </span>
                    <span className={i <= stageIndex ? "text-ink" : "text-ink-muted"}>{stage}</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="px-4 py-3 border-t border-hairline bg-surface">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={placeholder}
            disabled={loading}
            className="flex-1 rounded-lg border border-hairline px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-citation disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-ink text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-citation disabled:opacity-40 transition-colors"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
