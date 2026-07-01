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
    <div className="flex flex-col h-screen">
      <header className="shrink-0 border-b border-hairline bg-surface px-4 py-2.5">
        <div className="flex items-baseline justify-between gap-3">
          <div>
            <h1 className="font-display italic font-semibold text-lg">Contract Intelligence Assistant</h1>
            <p className="text-xs text-ink-muted">Live Demo — cited answers over your contracts</p>
          </div>
        </div>
        <p className="text-xs text-ink-muted mt-1">
          Uploads here are processed on the spot. In production, this would sync automatically from your
          document management system (SharePoint, Google Drive, or a DMS like NetDocuments) instead of
          manual upload.
        </p>
      </header>

      <div className="flex flex-1 min-h-0">
        <div className="w-72 shrink-0 border-r border-hairline bg-surface flex flex-col">
          <DocumentSidebar
            selectedDocId={selectedDoc?.doc_id ?? null}
            onSelectDoc={setSelectedDoc}
          />
        </div>

        <div className="flex-1 flex flex-col min-w-0">
          <ChatPanel
            scopedDocId={selectedDoc?.doc_id ?? null}
            scopedDocName={selectedDoc?.doc_name ?? null}
            onCitationClick={setActiveCitation}
            onClearScope={() => setSelectedDoc(null)}
          />
        </div>

        <CitationDrawer
          citation={activeCitation}
          onClose={() => setActiveCitation(null)}
        />
      </div>
    </div>
  );
}
