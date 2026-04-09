import {
  ComplianceService,
  FeedbackService,
  HumanInLoopService,
  MonitoringService,
  OpenAPI,
  OutputService,
  type AuditEntry,
  type ConfirmPayload,
  type FeedbackPayload,
  type GatedRecommendation,
  type MonitoringIngestResponse,
  type PerformanceSnapshot,
  type StatisticalDriftReport,
} from "@/lib/api/generated";

function configureOpenApi(): void {
  OpenAPI.BASE =
    process.env.INTERNAL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}

export async function getLatestRecommendation(patientId: string): Promise<GatedRecommendation> {
  configureOpenApi();
  return OutputService.getLatestRecommendationOutputLatestRecommendationGet(patientId);
}

export async function getMonitoringDrift(): Promise<StatisticalDriftReport> {
  configureOpenApi();
  return MonitoringService.getLatestDriftMonitoringDriftGet();
}

export async function getMonitoringPerformance(): Promise<PerformanceSnapshot> {
  configureOpenApi();
  return MonitoringService.getLatestPerformanceMonitoringPerformanceGet();
}

export async function getAuditTrail(offset = 0, limit = 20): Promise<AuditEntry[]> {
  configureOpenApi();
  return ComplianceService.getAuditTrailComplianceAuditTrailGet(offset, limit);
}

export async function confirmRecommendation(payload: ConfirmPayload) {
  configureOpenApi();
  return HumanInLoopService.confirmRecommendationGateConfirmPost(payload);
}

export async function overrideRecommendation(payload: {
  clinician_id: string;
  recommendation_id: string;
  reason: string;
}) {
  configureOpenApi();
  return HumanInLoopService.overrideRecommendationGateOverridePost(payload);
}

export async function sendFeedback(payload: FeedbackPayload) {
  configureOpenApi();
  return FeedbackService.postFeedbackFeedbackPost(payload);
}

export async function ingestMonitoring(payload: {
  reference: Array<Record<string, number>>;
  current: Array<Record<string, number>>;
  predictions: number[];
  ground_truth: number[];
  sensitive_attrs: number[];
  error_rate: number;
}): Promise<MonitoringIngestResponse> {
  configureOpenApi();
  return MonitoringService.ingestMonitoringMonitoringIngestPost(payload);
}

