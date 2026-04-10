"use client";

import { useEffect, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getPatientPrescriptions, type Prescription } from "@/lib/chat-api";

interface PrescriptionCardProps {
  patientId: string;
}

export function PrescriptionCard({ patientId }: PrescriptionCardProps): JSX.Element {
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);

  useEffect(() => {
    void getPatientPrescriptions(patientId)
      .then(setPrescriptions)
      .catch(() => setPrescriptions([]));
  }, [patientId]);

  return (
    <Card className="mt-4">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Recent Prescriptions</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-xs text-slate-700">
        {prescriptions.length === 0 ? (
          <p className="text-slate-500">No prescriptions found.</p>
        ) : (
          prescriptions.map((rx) => (
            <div key={rx.id} className="rounded border border-slate-200 bg-slate-50 p-2">
              {(rx.medications ?? []).map((med, idx) => (
                <div key={`${rx.id}-${idx}`} className="mb-1 last:mb-0">
                  <p className="font-medium">{med.name ?? "Medication"}</p>
                  <p>
                    {med.dose ?? "N/A"} | {med.frequency ?? "N/A"} | {med.duration ?? "N/A"}
                  </p>
                </div>
              ))}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

