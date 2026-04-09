import { ActionPanel } from "@/components/dashboard/action-panel";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getLatestRecommendation } from "@/lib/api/client";

export default async function DashboardTreatmentPage({
  searchParams,
}: {
  searchParams: { patient_id?: string };
}): Promise<JSX.Element> {
  const patientId = searchParams.patient_id ?? "patient-001";
  const gated = await getLatestRecommendation(patientId);
  const recommendations = gated.recommendation.treatment?.recommendations ?? [];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Treatment Plan</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {recommendations.map((item, idx) => (
            <div key={`${item.intervention}-${idx}`} className="rounded-md border p-3">
              <p className="text-sm font-medium">{item.intervention}</p>
              <div className="mt-2 flex items-center gap-2">
                <Badge variant="default">{item.guideline_source}</Badge>
                <Badge variant="success">Evidence {item.evidence_level}</Badge>
              </div>
            </div>
          ))}
          <ActionPanel recommendation={gated} patientId={patientId} />
        </CardContent>
      </Card>
    </div>
  );
}

