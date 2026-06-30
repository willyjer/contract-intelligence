"""
Explicit tests for the "I don't know" path.

All three cases must return found=False. The sole arbiter of relevance is Claude's
INSUFFICIENT_CONTEXT sentinel — there is no score-threshold gate. Retrieval always
returns the top-K candidates; Claude decides if they answer the question.

Usage:
  python scripts/test_idontknow.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from app.services.retrieval import search
from app.services.generation import generate

AMBIGUOUS_DOC_ID = "5d19f4f2-97b4-506d-94e1-74656034f70d"
NDA_DOC_ID = "5155934b-b595-5c19-94f2-508a17aad8c3"

TEST_CASES = [
    {
        "label": "Path B — payment terms reference missing Exhibit A",
        "question": "What is the payment amount in the ambiguous vendor agreement?",
        "doc_id": AMBIGUOUS_DOC_ID,
        "expected_path": "B",
    },
    {
        "label": "Path B — termination period is 'reasonable notice' (undefined)",
        "question": "What is the exact termination notice period in the ambiguous vendor agreement?",
        "doc_id": AMBIGUOUS_DOC_ID,
        "expected_path": "B",
    },
    {
        "label": "Non-sequitur — unrelated question, Claude returns INSUFFICIENT_CONTEXT",
        "question": "What is the square footage of the office in the NDA?",
        "doc_id": None,
        "expected_path": "B",
    },
]


def run_tests() -> None:
    passed = 0
    failed = 0

    for i, case in enumerate(TEST_CASES, start=1):
        print(f"\n[{i}/3] {case['label']}")
        print(f"      Q: {case['question']}")

        chunks = search(case["question"], doc_id=case.get("doc_id"))
        print(f"      Retrieved {len(chunks)} chunks", end="")
        if chunks:
            print(f" (top score: {chunks[0].score:.3f})")
        else:
            print()

        response = generate(case["question"], chunks)

        if response.found:
            print(f"      FAIL: expected found=False but got found=True")
            print(f"      answer: {response.answer[:120]}")
            failed += 1
        else:
            print(f"      PASS: found=False — \"{response.answer}\"")
            passed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed}/3 passed, {failed}/3 failed")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
