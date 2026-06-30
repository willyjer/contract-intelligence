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
      <div className="absolute inset-0 bg-black/20" onClick={onClose} />
      <div className="relative w-full max-w-md bg-white shadow-xl flex flex-col h-full">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
          <div>
            <p className="font-semibold text-gray-800 text-sm">{citation.doc_name}</p>
            <p className="text-xs text-gray-500">Page {citation.page_number}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
            aria-label="Close"
          >
            ×
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
            Source excerpt
          </p>
          <blockquote className="bg-yellow-50 border-l-4 border-yellow-400 px-4 py-3 text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
            {citation.snippet}
          </blockquote>
        </div>
      </div>
    </div>
  );
}
