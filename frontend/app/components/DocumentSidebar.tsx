"use client";
import { useEffect, useRef, useState } from "react";
import type { DocumentDetail, DocumentSummary } from "@/app/lib/api";
import { getDocument, listDocuments, uploadDocument } from "@/app/lib/api";
import ExtractionPanel from "./ExtractionPanel";

interface Props {
  selectedDocId: string | null;
  onSelectDoc: (doc: DocumentSummary | null) => void;
}

export default function DocumentSidebar({ selectedDocId, onSelectDoc }: Props) {
  const [docs, setDocs] = useState<DocumentSummary[]>([]);
  const [detail, setDetail] = useState<DocumentDetail | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
    try {
      const result = await uploadDocument(file);
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
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200 bg-white flex items-center justify-between">
        <h2 className="font-semibold text-gray-800">Documents</h2>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="text-xs bg-blue-600 text-white rounded px-2.5 py-1.5 hover:bg-blue-700 disabled:opacity-50 transition-colors"
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

      {uploadError && (
        <div className="mx-3 mt-2 text-xs bg-red-50 border border-red-200 text-red-700 rounded px-3 py-2">
          {uploadError}
        </div>
      )}

      <div className="flex-1 overflow-y-auto">
        {docs.length === 0 && (
          <p className="text-sm text-gray-400 px-4 pt-4">No documents loaded.</p>
        )}
        {docs.map((doc) => {
          const isSelected = selectedDocId === doc.doc_id;
          return (
            <button
              key={doc.doc_id}
              onClick={() => handleDocClick(doc)}
              className={`w-full text-left px-4 py-3 border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                isSelected ? "bg-blue-50 border-l-4 border-l-blue-500" : ""
              }`}
            >
              <p className={`text-sm font-medium truncate ${isSelected ? "text-blue-700" : "text-gray-700"}`}>
                {doc.doc_name}
              </p>
              <p className="text-xs text-gray-400 mt-0.5 uppercase">{doc.doc_type}</p>
            </button>
          );
        })}
      </div>

      {detail && selectedDocId && (
        <div className="border-t border-gray-200 p-4 overflow-y-auto max-h-80">
          <ExtractionPanel docName={detail.doc_name} fields={detail.extracted_fields} />
        </div>
      )}
    </div>
  );
}
