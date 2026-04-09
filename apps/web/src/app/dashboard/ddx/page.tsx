import { ActionPanel } from "@/components/dashboard/action-panel";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getLatestRecommendation } from "@/lib/api/client";

export default async function DashboardDdxPage({
  searchParams,
}: {
  searchParams: { patient_id?: string };
}): Promise<JSX.Element> {
  const patientId = searchParams.patient_id ?? "patient-001";
  const gated = await getLatestRecommendation(patientId);
  const shap = gated.recommendation.explanations?.tabular?.shap?.feature_importances ?? {};
  const diagnoses = gated.recommendation.ddx?.diagnoses ?? [];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Differential Diagnosis</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {diagnoses.map((dx) => (
            <div key={`${dx.icd10_code}-${dx.name}`} className="rounded-md border p-3">
              <div className="mb-1 flex items-center justify-between">
                <p className="text-sm font-medium">{dx.name}</p>
                <p className="text-xs text-slate-600">{dx.confidence.toFixed(2)}</p>
              </div>
              <Progress value={dx.confidence * 100} />
              <p className="mt-2 text-xs text-slate-600">ICD-10: {dx.icd10_code}</p>
            </div>
          ))}
          <div>
            <p className="mb-2 text-sm font-medium text-slate-800">SHAP Feature Importance</p>
            <div className="space-y-1">
              {Object.entries(shap).map(([k, v]) => (
                <p key={k} className="text-xs text-slate-600">
                  {k}: {v.toFixed(3)}
                </p>
              ))}
            </div>
          </div>
          <ActionPanel recommendation={gated} patientId={patientId} />
        </CardContent>
      </Card>
    </div>
  );
}

