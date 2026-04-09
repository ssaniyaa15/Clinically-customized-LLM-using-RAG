/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PerformanceSnapshot } from './PerformanceSnapshot';
import type { RetriggerEvent } from './RetriggerEvent';
import type { StatisticalDriftReport } from './StatisticalDriftReport';
export type MonitoringIngestResponse = {
    drift_report: StatisticalDriftReport;
    performance: PerformanceSnapshot;
    concept_drift: Record<string, boolean>;
    retrigger_event: (RetriggerEvent | null);
};

