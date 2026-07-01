"use client";
import { useEffect, useRef, useState } from "react";
import type { DocumentDetail, DocumentSummary } from "@/app/lib/api";
import { getDocument, listDocuments, uploadDocument } from "@/app/lib/api";
import ExtractionPanel from "./ExtractionPanel";

interface Props {
  selectedDocId: string | null;
  onSelectDoc: (doc: DocumentSummary | null) => void;
}

const UPLOAD_STAGES = [
  "Reading document…",
  "Extracting text…",
  "Chunking for search…",
  "Extracting key fields…",
  "Ready to query…",
];
const STAGE_MS = 550;

export default function DocumentSidebar({ selectedDocId, onSelectDoc }: Props) {
  const [docs, setDocs] = useState<DocumentSummary[]>([]);
  const [detail, setDetail] = useState<DocumentDetail | null>(null);
  const [uploading, setUploading] = useState(false);
  const [stageIndex, setStageIndex] = useState(-1);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    listDocuments().then(setDocs).catch(console.error);
  }, []);

  async function handleDocClick(doc: DocumentSummary) {
    if (selectedDocId === doc.doc_id) {
      onSelectDoc(null);
      setDetail(null);
      return;
    }
    onSelectDoc(doc);
    try {
      const d = await getDocument(doc.doc_id);
      setDetail(d);
    } catch {
      setDetail(null);
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    setStageIndex(0);

    timerRef.current = setInterval(() => {
      setStageIndex((i) => (i < UPLOAD_STAGES.length - 1 ? i + 1 : i));
    }, STAGE_MS);

    // Same pattern as the query narration: wait for both the real upload
    // and the full staged sequence so neither a fast nor a slow response
    // desyncs from what the checklist is showing.
    const minimumSequence = new Promise<void>((resolve) => setTimeout(resolve, UPLOAD_STAGES.length * STAGE_MS));

    try {
      const [result] = await Promise.all([uploadDocument(file), minimumSequence]);
      const updated = await listDocuments();
      setDocs(updated);
      const newDoc = updated.find((d) => d.doc_id === result.doc_id);
      if (newDoc) {
        onSelectDoc(newDoc);
        const d = await getDocument(result.doc_id);
        setDetail(d);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Upload failed";
      const isRateLimit = msg.includes("per 1 hour") || msg.includes("rate_limit");
      setUploadError(
        isRateLimit ? "Upload limit reached (5/hour). Try again later." : msg
      );
    } finally {
      if (timerRef.current) clearInterval(timerRef.current);
      setUploading(false);
      setStageIndex(-1);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="px-4 py-3 border-b border-hairline bg-surface flex items-center justify-between">
        <h2 className="font-display italic text-ink">Documents</h2>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="text-xs bg-ink text-white rounded px-2.5 py-1.5 hover:bg-citation disabled:opacity-50 transition-colors"
        >
          {uploading ? "Uploading…" : "+ Upload"}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          className="hidden"
          onChange={handleUpload}
        />
      </div>

      {uploading && (
        <div className="mx-3 mt-2 bg-highlight-soft border border-hairline rounded-md px-3 py-2">
          <ol className="flex flex-col gap-1">
            {UPLOAD_STAGES.map((stage, i) => (
              <li key={stage} className="flex items-center gap-2 text-xs">
                <span
                  className={`w-3 h-3 rounded-full border flex items-center justify-center shrink-0 ${
                    i < stageIndex
                      ? "bg-verified border-verified text-white"
                      : i === stageIndex
                        ? "border-citation animate-pulse"
                        : "border-hairline"
                  }`}
                  aria-hidden
                >
                  {i < stageIndex && <span className="text-[0.4rem]">✓</span>}
                </span>
                <span className={i <= stageIndex ? "text-ink" : "text-ink-muted"}>{stage}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {uploadError && (
        <div className="mx-3 mt-2 text-xs bg-redline-soft border border-redline text-redline rounded px-3 py-2">
          {uploadError}
        </div>
      )}

      <div className="flex-1 overflow-y-auto">
        {docs.length === 0 && (
          <p className="text-sm text-ink-muted px-4 pt-4">No documents loaded.</p>
        )}
        {docs.map((doc) => {
          const isSelected = selectedDocId === doc.doc_id;
          return (
            <button
              key={doc.doc_id}
              onClick={() => handleDocClick(doc)}
              className={`w-full text-left px-4 py-3 border-b border-hairline hover:bg-highlight-soft/40 transition-colors ${
                isSelected ? "bg-highlight-soft border-l-4 border-l-citation" : ""
              }`}
            >
              <p className={`text-sm font-medium truncate ${isSelected ? "text-citation" : "text-ink"}`}>
                {doc.doc_name}
              </p>
              <p className="text-xs text-ink-muted mt-0.5 uppercase font-data">{doc.doc_type}</p>
            </button>
          );
        })}
      </div>

      {detail && selectedDocId && (
        <div className="border-t border-hairline p-4 overflow-y-auto max-h-80">
          <ExtractionPanel docName={detail.doc_name} fields={detail.extracted_fields} />
        </div>
      )}
    </div>
  );
}
