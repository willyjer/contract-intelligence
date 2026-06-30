"use client";
import type { CitationRef, QueryResponse } from "@/app/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  response?: QueryResponse;
}

interface Props {
  message: Message;
  onCitationClick: (citation: CitationRef) => void;
}

function renderAnswerWithCitations(
  answer: string,
  citations: CitationRef[],
  onCitationClick: (c: CitationRef) => void
) {
  const parts = answer.split(/(\[\d+\])/g);
  return parts.map((part, i) => {
    const match = part.match(/^\[(\d+)\]$/);
    if (match) {
      const num = parseInt(match[1]);
      const citation = citations.find((c) => c.number === num);
      if (citation) {
        return (
          <button
            key={i}
            onClick={() => onCitationClick(citation)}
            className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-blue-100 text-blue-700 text-xs font-bold hover:bg-blue-200 transition-colors mx-0.5 align-baseline"
            title={`${citation.doc_name}, Page ${citation.page_number}`}
          >
            {num}
          </button>
        );
      }
    }
    return <span key={i}>{part}</span>;
  });
}

export default function MessageBubble({ message, onCitationClick }: Props) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm">
          {message.content}
        </div>
      </div>
    );
  }

  const response = message.response;
  const isNotFound = response && !response.found;

  return (
    <div className="flex justify-start">
      <div
        className={`max-w-[85%] rounded-2xl rounded-tl-sm px-4 py-3 text-sm leading-relaxed ${
          isNotFound
            ? "bg-amber-50 border border-amber-200 text-amber-900"
            : "bg-gray-100 text-gray-800"
        }`}
      >
        {isNotFound && (
          <p className="text-xs font-semibold text-amber-600 mb-1 uppercase tracking-wide">
            Not found in documents
          </p>
        )}
        <div className="whitespace-pre-wrap">
          {response && response.found && response.citations.length > 0
            ? renderAnswerWithCitations(response.answer, response.citations, onCitationClick)
            : message.content}
        </div>
      </div>
    </div>
  );
}

export type { Message };
