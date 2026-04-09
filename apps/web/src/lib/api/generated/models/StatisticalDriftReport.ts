/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DriftResult } from './DriftResult';
import type { PSIResult } from './PSIResult';
export type StatisticalDriftReport = {
    ks_results?: Record<string, DriftResult>;
    psi_results?: Record<string, PSIResult>;
    mmd_result: DriftResult;
    kl_results?: Record<string, number>;
};

