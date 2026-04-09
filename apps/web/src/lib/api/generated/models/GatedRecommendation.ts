/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ClinicalRecommendation_Output } from './ClinicalRecommendation_Output';
export type GatedRecommendation = {
    recommendation: ClinicalRecommendation_Output;
    requires_confirmation?: boolean;
    escalation_level: GatedRecommendation.escalation_level;
    override_allowed?: boolean;
    safety_warning?: (string | null);
};
export namespace GatedRecommendation {
    export enum escalation_level {
        ROUTINE = 'routine',
        URGENT = 'urgent',
        CRITICAL = 'critical',
    }
}

