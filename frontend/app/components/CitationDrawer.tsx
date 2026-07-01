"use client";
import type { CitationRef } from "@/app/lib/api";

interface Props {
  citation: CitationRef | null;
  onClose: () => void;
}

export default function CitationDrawer({ citation, onClose }: Props) {
  if (!citation) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-ink/20" onClick={onClose} />
      <div className="relative w-full max-w-md bg-surface shadow-xl flex flex-col h-full">
        <div className="flex items-center justify-between px-4 py-3 border-b border-hairline">
          <div>
            <p className="font-display italic text-ink text-sm">{citation.doc_name}</p>
            <p className="text-xs text-ink-muted font-data">Page {citation.page_number}</p>
          </div>
          <button
            onClick={onClose}
            className="text-ink-muted hover:text-ink text-xl leading-none"
            aria-label="Close"
          >
            ×
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          <p className="text-xs font-data uppercase tracking-wide text-ink-muted mb-2">
            Source excerpt
          </p>
          {/* key forces a remount so the highlight-sweep animation replays for each new citation */}
          <blockquote
            key={`${citation.doc_name}-${citation.page_number}-${citation.number}`}
            className="border-l-4 border-citation pl-4 py-1 text-sm text-ink whitespace-pre-wrap leading-relaxed"
          >
            <span className="citation-highlight">{citation.snippet}</span>
          </blockquote>
        </div>
      </div>
    </div>
  );
}
