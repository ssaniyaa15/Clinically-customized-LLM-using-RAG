/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DDxOutput } from './DDxOutput';
import type { ExplanationBundle } from './ExplanationBundle';
import type { RiskPrognosisOutput } from './RiskPrognosisOutput';
import type { TreatmentPlan } from './TreatmentPlan';
export type ClinicalRecommendation_Input = {
    ddx: DDxOutput;
    treatment: TreatmentPlan;
    risk: RiskPrognosisOutput;
    explanations: Record<string, ExplanationBundle>;
    generated_at: string;
    uncertainty_score: number;
};

