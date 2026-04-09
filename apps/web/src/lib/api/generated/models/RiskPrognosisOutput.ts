/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ComplicationRisks } from './ComplicationRisks';
import type { ReadmissionRisk } from './ReadmissionRisk';
import type { SurvivalCurve } from './SurvivalCurve';
export type RiskPrognosisOutput = {
    readmission: ReadmissionRisk;
    survival: SurvivalCurve;
    complications: ComplicationRisks;
};

