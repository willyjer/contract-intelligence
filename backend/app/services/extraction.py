import json
import logging

import anthropic
from qdrant_client import QdrantClient

from app.config import settings

logger = logging.getLogger(__name__)

claude_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
qdrant_client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)

CLAUDE_MODEL = "claude-haiku-4-5-20251001"
DOCS_COLLECTION = "contract_documents"

EXTRACTION_PROMPT = """Extract structured data from the contract below. Return a JSON object with exactly these fields and no other text:

{
  "parties": [],
  "effective_date": null,
  "termination_clause": null,
  "payment_terms": null,
  "governing_law": null,
  "non_compete": null,
  "ambiguous_or_missing": []
}

Field rules:
- parties: list of strings, each party's full name
- effective_date: ISO 8601 date string (e.g. "2024-01-01") if explicitly stated, otherwise null
- termination_clause: verbatim quote of the termination/notice clause, or null if absent
- payment_terms: plain-language description of payment terms (rate, schedule, due date), or null if absent
- governing_law: jurisdiction name only (e.g. "Delaware"), or null if not specified
- non_compete: true if an explicit non-compete or restrictive covenant clause exists, false if the contract explicitly states there is none, null if neither
- ambiguous_or_missing: list of strings, one per field that is unclear, vague, or references missing content (e.g. "Payment terms reference Exhibit A which is not present")

Only use information present in the document. Do not guess or infer. Return only the JSON object."""


def _fetch_full_text(doc_id: str) -> str | None:
    results = qdrant_client.retrieve(
        collection_name=DOCS_COLLECTION,
        ids=[doc_id],
        with_payload=True,
        with_vectors=False,
    )
    if not results:
        return None
    return results[0].payload.get("full_text")


def extract_fields(doc_id: str) -> dict:
    full_text = _fetch_full_text(doc_id)
    if not full_text:
        logger.warning("extract_fields: doc_id=%s not found in contract_documents", doc_id)
        return {}

    message = claude_client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"{EXTRACTION_PROMPT}\n\n---\n\n{full_text}",
            }
        ],
    )
    raw = message.content[0].text.strip()

    # Claude sometimes wraps JSON in ```json ... ``` fences — strip them.
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw[: raw.rfind("```")]
        raw = raw.strip()

    try:
        fields = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning(
            "extraction_json_parse_failed doc_id=%s raw_preview=%r", doc_id, raw[:200]
        )
        fields = {"_raw": raw, "ambiguous_or_missing": ["Extraction output was not valid JSON"]}

    qdrant_client.set_payload(
        collection_name=DOCS_COLLECTION,
        payload={"extracted_fields": json.dumps(fields)},
        points=[doc_id],
    )
    logger.info("extract_fields: stored fields for doc_id=%s", doc_id)
    return fields
