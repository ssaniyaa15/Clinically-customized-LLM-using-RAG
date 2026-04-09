/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { MonitoringIngestResponse } from '../models/MonitoringIngestResponse';
import type { MonitoringPayload } from '../models/MonitoringPayload';
import type { PerformanceSnapshot } from '../models/PerformanceSnapshot';
import type { StatisticalDriftReport } from '../models/StatisticalDriftReport';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class MonitoringService {
    /**
     * Get Latest Drift
     * @returns StatisticalDriftReport Successful Response
     * @throws ApiError
     */
    public static getLatestDriftMonitoringDriftGet(): CancelablePromise<StatisticalDriftReport> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/monitoring/drift',
        });
    }
    /**
     * Get Latest Performance
     * @returns PerformanceSnapshot Successful Response
     * @throws ApiError
     */
    public static getLatestPerformanceMonitoringPerformanceGet(): CancelablePromise<PerformanceSnapshot> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/monitoring/performance',
        });
    }
    /**
     * Ingest Monitoring
     * @param requestBody
     * @returns MonitoringIngestResponse Successful Response
     * @throws ApiError
     */
    public static ingestMonitoringMonitoringIngestPost(
        requestBody: MonitoringPayload,
    ): CancelablePromise<MonitoringIngestResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/monitoring/ingest',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
