import logging
import re
from dataclasses import dataclass, field

import anthropic

from app.config import settings
from app.services.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)

claude_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

CLAUDE_MODEL = "claude-haiku-4-5-20251001"
NOT_FOUND_MESSAGE = "I couldn't find this information in the provided documents."
INSUFFICIENT_CONTEXT_SENTINEL = "INSUFFICIENT_CONTEXT:"

SYSTEM_PROMPT = """You are a contract analysis assistant. Answer questions using ONLY the provided contract excerpts.
Cite each excerpt you use as [1], [2], etc., matching the numbers in the provided list.
If the provided excerpts do not contain enough information to answer the question, respond with exactly:
"INSUFFICIENT_CONTEXT: I couldn't find this information in the provided documents."
Do not guess, infer, or use outside knowledge.
Write in plain text only. Do not use markdown formatting such as bold, italics, bullet points, or headers."""


@dataclass
class CitationRef:
    number: int
    doc_name: str
    page_number: int
    snippet: str


@dataclass
class QueryResponse:
    answer: str
    found: bool
    citations: list[CitationRef] = field(default_factory=list)


def _build_user_message(question: str, chunks: list[RetrievedChunk]) -> str:
    excerpts = "\n".join(
        f'[{i + 1}] "{c.chunk_text}" — {c.doc_name}, Page {c.page_number}'
        for i, c in enumerate(chunks)
    )
    return f"Question: {question}\n\nContract excerpts:\n{excerpts}\n\nAnswer:"


def _parse_citations(
    response_text: str, chunks: list[RetrievedChunk]
) -> list[CitationRef]:
    try:
        numbers = [int(n) for n in re.findall(r"\[(\d+)\]", response_text)]
        numbers = sorted(set(numbers))
        citations = []
        for n in numbers:
            idx = n - 1  # [1] maps to chunks[0]
            if 0 <= idx < len(chunks):
                c = chunks[idx]
                citations.append(
                    CitationRef(
                        number=n,
                        doc_name=c.doc_name,
                        page_number=c.page_number,
                        snippet=c.chunk_text,
                    )
                )
            else:
                logger.warning(
                    "citation_out_of_range number=%d total_chunks=%d response_preview=%r",
                    n,
                    len(chunks),
                    response_text[:120],
                )
        return citations
    except Exception:
        logger.warning(
            "citation_parse_failed response_preview=%r", response_text[:120]
        )
        return []


def generate(question: str, chunks: list[RetrievedChunk]) -> QueryResponse:
    # Path A: retrieval found nothing above the score threshold — skip Claude entirely.
    if not chunks:
        logger.info("not_found_path=A question=%r", question[:80])
        return QueryResponse(answer=NOT_FOUND_MESSAGE, found=False)

    user_message = _build_user_message(question, chunks)

    message = claude_client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    response_text = message.content[0].text.strip()

    # Path B: chunks were retrieved but don't answer the question.
    if response_text.startswith(INSUFFICIENT_CONTEXT_SENTINEL):
        logger.info("not_found_path=B question=%r", question[:80])
        return QueryResponse(answer=NOT_FOUND_MESSAGE, found=False)

    citations = _parse_citations(response_text, chunks)
    logger.info(
        "generation result=found citations=%d question=%r",
        len(citations),
        question[:80],
    )
    return QueryResponse(answer=response_text, found=True, citations=citations)
