"use client";
import { useState } from "react";
import type { CitationRef, DocumentSummary } from "@/app/lib/api";
import ChatPanel from "./components/ChatPanel";
import CitationDrawer from "./components/CitationDrawer";
import DocumentSidebar from "./components/DocumentSidebar";

export default function Home() {
  const [selectedDoc, setSelectedDoc] = useState<DocumentSummary | null>(null);
  const [activeCitation, setActiveCitation] = useState<CitationRef | null>(null);

  return (
    <div className="flex h-screen bg-gray-50 font-sans">
      {/* Left pane */}
      <div className="w-72 shrink-0 border-r border-gray-200 bg-white flex flex-col">
        <DocumentSidebar
          selectedDocId={selectedDoc?.doc_id ?? null}
          onSelectDoc={setSelectedDoc}
        />
      </div>

      {/* Right pane */}
      <div className="flex-1 flex flex-col min-w-0">
        <ChatPanel
          scopedDocId={selectedDoc?.doc_id ?? null}
          scopedDocName={selectedDoc?.doc_name ?? null}
          onCitationClick={setActiveCitation}
        />
      </div>

      <CitationDrawer
        citation={activeCitation}
        onClose={() => setActiveCitation(null)}
      />
    </div>
  );
}
