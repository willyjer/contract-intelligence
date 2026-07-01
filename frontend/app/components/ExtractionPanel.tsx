"use client";
import type { ExtractedFields } from "@/app/lib/api";

interface Props {
  docName: string;
  fields: ExtractedFields;
}

function FieldRow({ label, value }: { label: string; value: React.ReactNode }) {
  const isMissing = value === "—";
  return (
    <div className="py-2 border-b border-hairline last:border-0 text-sm">
      <div className="flex items-center justify-between gap-2">
        <span className="text-ink-muted">{label}</span>
        <span
          className={`shrink-0 whitespace-nowrap font-data text-[0.65rem] uppercase tracking-wide ${
            isMissing ? "text-redline" : "text-verified"
          }`}
        >
          {isMissing ? "⚠ missing" : "✓ extracted"}
        </span>
      </div>
      <p className="text-ink break-words mt-0.5">{value}</p>
    </div>
  );
}

export default function ExtractionPanel({ docName, fields }: Props) {
  if (fields._raw) {
    return (
      <div className="mt-4 p-3 bg-redline-soft border border-redline rounded text-sm text-redline">
        Field extraction unavailable for this document.
      </div>
    );
  }

  const boolLabel = (v: boolean | null | undefined) =>
    v === true ? "Yes" : v === false ? "No" : "—";

  return (
    <div className="mt-4">
      <p className="text-xs font-data uppercase tracking-wide text-ink-muted mb-2">
        Auto-extracted fields
      </p>
      <div className="bg-surface border border-hairline rounded-lg p-3">
        <FieldRow label="Parties" value={fields.parties?.join(", ") || "—"} />
        <FieldRow label="Effective date" value={fields.effective_date ?? "—"} />
        <FieldRow label="Termination" value={fields.termination_clause ?? "—"} />
        <FieldRow label="Payment terms" value={fields.payment_terms ?? "—"} />
        <FieldRow label="Governing law" value={fields.governing_law ?? "—"} />
        <FieldRow label="Non-compete" value={boolLabel(fields.non_compete)} />
      </div>

      {fields.ambiguous_or_missing && fields.ambiguous_or_missing.length > 0 && (
        <div className="mt-2 space-y-1">
          {fields.ambiguous_or_missing.map((note, i) => (
            <div
              key={i}
              className="flex gap-1.5 items-start text-xs bg-redline-soft border border-redline text-redline rounded px-2 py-1.5"
            >
              <span className="mt-0.5 shrink-0">⚠</span>
              <span>{note}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
