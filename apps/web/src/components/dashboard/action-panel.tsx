"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { confirmRecommendation, overrideRecommendation, sendFeedback } from "@/lib/api/client";
import { type GatedRecommendation, FeedbackPayload } from "@/lib/api/generated";

type Props = {
  recommendation: GatedRecommendation;
  patientId: string;
};

export function ActionPanel({ recommendation, patientId }: Props): JSX.Element {
  const [status, setStatus] = useState<string>("");
  const recommendationId = recommendation.recommendation.generated_at ?? new Date().toISOString();
  const clinicianId = "clinician-demo";

  async function onAccept(): Promise<void> {
    await confirmRecommendation({ clinician_id: clinicianId, recommendation_id: recommendationId, confirmed: true });
    await sendFeedback({
      recommendation_id: recommendationId,
      clinician_id: clinicianId,
      action: FeedbackPayload.action.ACCEPT,
      free_text: null,
      patient_id: patientId,
    });
    setStatus("Accepted and feedback submitted.");
  }

  async function onModify(): Promise<void> {
    await confirmRecommendation({ clinician_id: clinicianId, recommendation_id: recommendationId, confirmed: true });
    await sendFeedback({
      recommendation_id: recommendationId,
      clinician_id: clinicianId,
      action: FeedbackPayload.action.MODIFY,
      free_text: "Modified after review.",
      patient_id: patientId,
    });
    setStatus("Marked as modified and feedback submitted.");
  }

  async function onOverride(): Promise<void> {
    await overrideRecommendation({
      clinician_id: clinicianId,
      recommendation_id: recommendationId,
      reason: "Clinical override",
    });
    await sendFeedback({
      recommendation_id: recommendationId,
      clinician_id: clinicianId,
      action: FeedbackPayload.action.REJECT,
      free_text: "Override applied.",
      patient_id: patientId,
    });
    setStatus("Override submitted and feedback logged.");
  }

  return (
    <div className="space-y-3">
      {recommendation.requires_confirmation && (
        <div className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-800">
          Requires Confirmation
        </div>
      )}
      <div className="flex flex-wrap gap-2">
        <Button onClick={onAccept}>Accept</Button>
        <Button variant="secondary" onClick={onModify}>
          Modify
        </Button>
        <Button variant="destructive" onClick={onOverride}>
          Override
        </Button>
      </div>
      {status ? <p className="text-xs text-slate-600">{status}</p> : null}
    </div>
  );
}

