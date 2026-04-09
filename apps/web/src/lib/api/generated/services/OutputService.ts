/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GatedRecommendation } from '../models/GatedRecommendation';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class OutputService {
    /**
     * Get Latest Recommendation
     * @param patientId Patient identifier
     * @returns GatedRecommendation Successful Response
     * @throws ApiError
     */
    public static getLatestRecommendationOutputLatestRecommendationGet(
        patientId: string = 'patient-001',
    ): CancelablePromise<GatedRecommendation> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/output/latest-recommendation',
            query: {
                'patient_id': patientId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
