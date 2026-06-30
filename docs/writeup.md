# Contract Intelligence Assistant

**Live demo:** https://contract-intelligence-omega.vercel.app

---

## The Problem

Most contract Q&A demos fail in one of two ways. The common one is hallucination — the model gives a confident, cited-looking answer that doesn't actually appear in the document. The subtler one is false negatives: the system returns "not found" for information that *is* there, because it decided internally that the retrieved text wasn't relevant enough. Both erode trust, but the second is worse — it actively tells you something isn't true.

There's also a structural gap: Q&A and structured extraction are usually separate tools. You either ask free-form questions or you run an extraction pipeline. Contract review almost always requires both.

---

## What This Does

Upload a contract (PDF, DOCX, or TXT) and ask questions in plain language. The system retrieves the relevant clauses, generates an answer, and shows you exactly which page and which excerpt it's drawing from — not just a page number, but the quoted text, so you can verify the citation in seconds without opening the document.

When the answer isn't in the document, it says so clearly, with a distinct visual state. It doesn't guess, and it doesn't silently skip the question.

Every uploaded document is also automatically analyzed for key fields: parties, effective date, termination clause, payment terms, governing law, non-compete status. Fields that are missing or ambiguous are flagged explicitly rather than left blank.

Scanned PDFs are handled automatically. When a page has no extractable text, the system renders it as an image and runs it through Claude vision to extract the content before ingestion — no manual preprocessing required.

---

## Key Decisions

**Hybrid retrieval over pure semantic search.** Each chunk is stored with both a dense embedding (OpenAI text-embedding-3-small) and a BM25 sparse vector (FastEmbed). At query time, both are searched in parallel and fused with Reciprocal Rank Fusion inside Qdrant. The top 20 candidates then go through Cohere rerank-v3.5 before the final 6 reach Claude. Pure semantic search misses exact keyword matches — contract clause numbers, party names, specific dollar amounts — that BM25 catches. Reranking filters noise before it reaches the generation step.

**Letting Claude be the relevance gate.** The original design used a cosine similarity score to decide whether retrieved chunks were relevant enough to pass to the model. I removed it. Embedding distance doesn't reliably track "does this chunk answer the question?" — a realistic question about late payment penalties scored just below the threshold against a chunk that directly answered it. The system would have returned "not found" for something clearly in the document. Claude's `INSUFFICIENT_CONTEXT` response is a better gate because it reads meaning rather than measuring distance. The model has the context; it should make the call.

**Citations that prove themselves.** Each citation shows the doc name, page number, and the exact excerpt the model cited — not just a page number, but the quoted text. A visitor can verify in five seconds that the answer is actually supported by what's in the document.

**A visible "I don't know" state.** The ambiguous contract in the demo (missing Exhibit A, vague notice period) returns not-found for those fields. I designed a distinct UI state for this — amber styling, explicit label — because a system that hedges silently is less useful than one that signals clearly when it's uncertain. For contract work, where the cost of a missed clause is real, that distinction matters.

**Extraction at ingest time.** Structured field extraction runs automatically on upload. Parties, dates, payment terms, governing law, non-compete status — stored immediately and displayed when you select a document. Fields that are missing or ambiguous are flagged explicitly.

---

## What I'd Change at Scale

Rate limiting is per IP address. A real deployment needs per-user metering tied to an auth system — IP limits are meaningless in an enterprise network.

Document ingestion (embedding + extraction) runs synchronously during upload. For large files or concurrent uploads, this moves to a background queue.

Chunking is paragraph-level with section-heading detection. A clause-boundary-aware chunker trained on contract structure would improve retrieval precision in dense legal documents where a single clause spans multiple paragraphs.

There's no user-level data isolation. A multi-tenant deployment needs per-user or per-org namespacing in the vector store, with query filtering enforced at the API layer.
