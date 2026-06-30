"use client";
import { useEffect, useRef, useState } from "react";
import type { CitationRef } from "@/app/lib/api";
import { queryDocuments } from "@/app/lib/api";
import MessageBubble, { type Message } from "./MessageBubble";

interface Props {
  scopedDocId: string | null;
  scopedDocName: string | null;
  onCitationClick: (citation: CitationRef) => void;
}

export default function ChatPanel({ scopedDocId, scopedDocName, onCitationClick }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);

    try {
      const response = await queryDocuments(question, scopedDocId);
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
      setLoading(false);
    }
  }

  const placeholder = scopedDocName
    ? `Ask about "${scopedDocName}"…`
    : "Ask a question about any of the contracts…";

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-gray-200 bg-white">
        <h2 className="font-semibold text-gray-800">Chat with your contracts</h2>
        {scopedDocName && (
          <p className="text-xs text-blue-600 mt-0.5">Searching within: {scopedDocName}</p>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {messages.length === 0 && (
          <p className="text-sm text-gray-400 text-center mt-8">
            Ask a question about any of the preloaded contracts, or upload your own.
          </p>
        )}
        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} onCitationClick={onCitationClick} />
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-3 text-sm text-gray-500 animate-pulse">
              Thinking…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="px-4 py-3 border-t border-gray-200 bg-white">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={placeholder}
            disabled={loading}
            className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-blue-600 text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-40 transition-colors"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
