"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { Badge } from "@/components/ui/badge";

const PATIENTS = ["patient-001", "patient-002", "patient-003"];

export function PatientSelector(): JSX.Element {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const selected = searchParams.get("patient_id") ?? "patient-001";

  return (
    <div className="flex items-center gap-3">
      <label className="text-sm font-medium text-slate-600" htmlFor="patient">
        Patient
      </label>
      <select
        id="patient"
        className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
        value={selected}
        onChange={(e) => router.push(`${pathname}?patient_id=${encodeURIComponent(e.target.value)}`)}
      >
        {PATIENTS.map((p) => (
          <option key={p} value={p}>
            {p}
          </option>
        ))}
      </select>
      <Badge variant="default">Mock Selector</Badge>
    </div>
  );
}

