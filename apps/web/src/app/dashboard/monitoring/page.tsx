import { ActionPanel } from "@/components/dashboard/action-panel";
import { MonitoringChart } from "@/components/dashboard/monitoring-chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getLatestRecommendation, getMonitoringDrift, getMonitoringPerformance } from "@/lib/api/client";

export default async function DashboardMonitoringPage({
  searchParams,
}: {
  searchParams: { patient_id?: string };
}): Promise<JSX.Element> {
  const patientId = searchParams.patient_id ?? "patient-001";
  const [drift, perf, gated] = await Promise.all([
    getMonitoringDrift(),
    getMonitoringPerformance(),
    getLatestRecommendation(patientId),
  ]);
  const firstPsi = Object.values(drift.psi_results ?? {})[0]?.psi_score ?? 0;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Model Monitoring</CardTitle>
        </CardHeader>
        <CardContent>
          <MonitoringChart auc={perf.auc} psi={firstPsi} fairnessGap={perf.fairness_gap} />
          <div className="mt-4">
            <ActionPanel recommendation={gated} patientId={patientId} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

