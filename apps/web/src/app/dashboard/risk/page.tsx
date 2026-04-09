import { ActionPanel } from "@/components/dashboard/action-panel";
import { RiskChart } from "@/components/dashboard/risk-chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getLatestRecommendation } from "@/lib/api/client";

export default async function DashboardRiskPage({
  searchParams,
}: {
  searchParams: { patient_id?: string };
}): Promise<JSX.Element> {
  const patientId = searchParams.patient_id ?? "patient-001";
  const gated = await getLatestRecommendation(patientId);
  const rec = gated.recommendation;
  const risk = rec.risk;

  const timePoints = risk?.survival?.time_points ?? [];
  const probs = risk?.survival?.survival_probabilities ?? [];
  const survival = timePoints.map((t, idx) => ({
    t,
    s: probs[idx] ?? 0,
  }));

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Risk & Prognosis</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <RiskChart probability={risk?.readmission?.probability ?? 0} survival={survival} />
          <ActionPanel recommendation={gated} patientId={patientId} />
        </CardContent>
      </Card>
    </div>
  );
}

