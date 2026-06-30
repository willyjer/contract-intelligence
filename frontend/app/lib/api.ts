const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, init);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? body.error ?? `HTTP ${res.status}`);
  }
  return res.json();
}

// ---------- Types ----------

export interface DocumentSummary {
  doc_id: string;
  doc_name: string;
  doc_type: string;
  page_count: number;
  uploaded_at: string;
}

export interface ExtractedFields {
  parties?: string[];
  effective_date?: string | null;
  termination_clause?: string | null;
  payment_terms?: string | null;
  governing_law?: string | null;
  non_compete?: boolean | null;
  ambiguous_or_missing?: string[];
  _raw?: string;
}

export interface DocumentDetail {
  doc_id: string;
  doc_name: string;
  full_text: string;
  extracted_fields: ExtractedFields;
  page_count: number;
}

export interface CitationRef {
  number: number;
  doc_name: string;
  page_number: number;
  snippet: string;
}

export interface QueryResponse {
  answer: string;
  found: boolean;
  citations: CitationRef[];
}

// ---------- Calls ----------

export function listDocuments(): Promise<DocumentSummary[]> {
  return request("/documents");
}

export function getDocument(doc_id: string): Promise<DocumentDetail> {
  return request(`/documents/${doc_id}`);
}

export function uploadDocument(file: File): Promise<{ doc_id: string; doc_name: string; chunk_count: number }> {
  const form = new FormData();
  form.append("file", file);
  return request("/documents/upload", { method: "POST", body: form });
}

export function queryDocuments(question: string, doc_id: string | null): Promise<QueryResponse> {
  return request("/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, doc_id }),
  });
}
