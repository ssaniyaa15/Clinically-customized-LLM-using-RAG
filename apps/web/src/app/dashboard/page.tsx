import { ActionPanel } from "@/components/dashboard/action-panel";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getLatestRecommendation } from "@/lib/api/client";

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: { patient_id?: string };
}): Promise<JSX.Element> {
  const patientId = searchParams.patient_id ?? "patient-001";
  const gated = await getLatestRecommendation(patientId);
  const rec = gated.recommendation;
  const diagnoses = rec.ddx?.diagnoses ?? [];
  const top = diagnoses[0];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Latest Clinical Recommendation</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <Badge variant="default">{patientId}</Badge>
            <Badge variant={gated.escalation_level === "critical" ? "danger" : "warning"}>
              {gated.escalation_level}
            </Badge>
          </div>
          <p className="text-sm text-slate-700">
            Top differential diagnosis: <span className="font-medium">{top?.name ?? "N/A"}</span> (
            {top?.icd10_code ?? "-"}) with confidence {(top?.confidence ?? 0).toFixed(2)}.
          </p>
          <p className="text-sm text-slate-700">
            Readmission risk tier: <span className="font-medium">{rec.risk?.readmission?.risk_tier ?? "unknown"}</span>.
          </p>
          <ActionPanel recommendation={gated} patientId={patientId} />
        </CardContent>
      </Card>
    </div>
  );
}

