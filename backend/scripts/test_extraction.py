"""
Run structured field extraction on all 5 demo contracts and print results.

Usage:
  python scripts/test_extraction.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from app.services.extraction import extract_fields

DEMO_CONTRACTS = [
    ("5155934b-b595-5c19-94f2-508a17aad8c3", "NDA — Acme / Example"),
    ("fad41552-b511-56ff-a3cc-423b69dfa1db", "Vendor — TechCorp / Widgets"),
    ("67af34d2-c91c-5cb2-a367-775d13089062", "Services — Consulting / Client"),
    ("b653b514-3d11-51ee-ade4-14cec753e343", "Lease — Harbor / Startup"),
    ("5d19f4f2-97b4-506d-94e1-74656034f70d", "Ambiguous — Dynamic / Vague"),
]


def print_fields(label: str, fields: dict) -> None:
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    for key, value in fields.items():
        if key == "ambiguous_or_missing":
            if value:
                print(f"  [!] ambiguous_or_missing:")
                for item in value:
                    print(f"       - {item}")
            else:
                print(f"  [ok] ambiguous_or_missing: (none)")
        elif isinstance(value, list):
            print(f"  {key}: {', '.join(value) if value else '(empty)'}")
        else:
            display = str(value) if value is not None else "null"
            print(f"  {key}: {display}")


def main() -> None:
    passed = 0
    failed = 0

    for doc_id, label in DEMO_CONTRACTS:
        print(f"\nExtracting: {label}...")
        fields = extract_fields(doc_id)

        if not fields:
            print(f"  FAIL: no fields returned")
            failed += 1
            continue

        if "_raw" in fields:
            print(f"  FAIL: extraction returned non-JSON output")
            failed += 1
            continue

        print_fields(label, fields)
        passed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed}/{len(DEMO_CONTRACTS)} extracted successfully, {failed} failed")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
