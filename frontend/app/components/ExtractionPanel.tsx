"use client";
import type { ExtractedFields } from "@/app/lib/api";

interface Props {
  docName: string;
  fields: ExtractedFields;
}

function FieldRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex gap-2 py-1.5 border-b border-gray-100 last:border-0 text-sm">
      <span className="text-gray-500 w-36 shrink-0">{label}</span>
      <span className="text-gray-800 break-words">{value}</span>
    </div>
  );
}

export default function ExtractionPanel({ docName, fields }: Props) {
  if (fields._raw) {
    return (
      <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded text-sm text-amber-800">
        Field extraction unavailable for this document.
      </div>
    );
  }

  const boolLabel = (v: boolean | null | undefined) =>
    v === true ? "Yes" : v === false ? "No" : "—";

  return (
    <div className="mt-4">
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
        Auto-extracted fields
      </p>
      <div className="bg-white border border-gray-200 rounded-lg p-3">
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
              className="flex gap-1.5 items-start text-xs bg-amber-50 border border-amber-200 text-amber-800 rounded px-2 py-1.5"
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
