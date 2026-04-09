/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DiagnosticReportPayload } from '../models/DiagnosticReportPayload';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class FhirService {
    /**
     * Get Smart Manifest
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getSmartManifestFhirSmartManifestGet(): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/fhir/smart-manifest',
        });
    }
    /**
     * Post Diagnostic Report
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static postDiagnosticReportFhirDiagnosticReportPost(
        requestBody: DiagnosticReportPayload,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/fhir/diagnostic-report',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
